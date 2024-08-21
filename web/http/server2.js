const http = require('http');
const fs = require('fs');
const url = require('url');
const path = require('path');
const { spawn } = require('child_process');

// const serverIP = '123.125.19.139';   // 04
const serverIP = '111.198.54.249';  // 03
const drawnPort = 556;
const forwardPort = 6102;

const server = http.createServer((req, res) => {
    // 记录时间日志
    const requestTime = new Date();
    console.log(`[${requestTime.toISOString()}] Received ${req.method} request for ${req.url}`);

    // 解析请求的URL
    const parsedUrl = url.parse(req.url, true);

    // 获取请求的路径
    const pathname = parsedUrl.pathname;

    if (pathname === '/') {
        // 默认地址为根路径时，返回默认的HTML页面
        sendHtmlFile(res, 'index.html');
    } else if (pathname.startsWith('/stream/')) {
        // 流播放页面
        const rtspPath = pathname.replace('/stream/', '');
        if (rtspPath == 'all') {
            sendHtmlFile(res, 'allStream.html');
        } else {
            sendHtmlResponse(res, generateRtspHtml(`rtsp://${serverIP}:${drawnPort}/${rtspPath}`));
        }
    } else if (pathname.startsWith('/video/')) {
        const videoFileName = pathname.replace('/video/', '');
        const originalVideoFilePath = path.join('../bjsubway/outs/playback', videoFileName + '.mp4');
        const transcodedVideoFilePath = path.join('../bjsubway/outs/playback', videoFileName + '_transcoded.mp4');
    
        // Check if the original video file exists
        if (fs.existsSync(originalVideoFilePath)) {
            // Check if the transcoded video file exists
            if (!fs.existsSync(transcodedVideoFilePath)) {
                // Transcode the video to H.264
                const ffmpeg = spawn('ffmpeg', [
                    '-i', originalVideoFilePath,
                    '-c:v', 'libx264',
                    '-crf', '20',
                    '-preset', 'fast',
                    transcodedVideoFilePath
                ]);
    
                ffmpeg.on('exit', (code) => {
                    if (code === 0) {
                        // Serve the transcoded video file
                        serveVideo(res, transcodedVideoFilePath);
                        // Delete the original video file
                        // fs.unlinkSync(originalVideoFilePath);
                    } else {
                        // If transcoding fails, respond with a 500 error
                        res.writeHead(500, { 'Content-Type': 'text/plain' });
                        res.end('Internal Server Error');
                    }
                });
            } else {
                // Serve the existing transcoded video file
                serveVideo(res, transcodedVideoFilePath);
            }
        } else {
            // If the video file doesn't exist, respond with a 404 error
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('Video not found');
        }
    } else {
        // For other URLs, respond with a simple HTML page
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<html><body><h1>Page Not Find</h1></body></html>');
    }
});

// 设置服务器监听的端口
const IP = '172.17.104.72'
const PORT = 6101;
server.listen(PORT, () => {
    console.log(`Server is running on http://${IP}:${PORT}`);
});

// 生成HTML页面
function generateRtspHtml(rtsp) {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1, maximum-scale=1, minimum-scale=1, user-scalable=no,viewport-fit=cover"
        />
        <script src="https://jsmpeg.com/jsmpeg.min.js" charset="utf-8"></script>
        <title>播放rtsp</title>
    </head>
    <body>
        <canvas id="canvas-1"></canvas>
    </body>
    <script>
        var rtsp = '${rtsp}'
        window.onload = () => {
            // 将rtsp视频流地址进行btoa处理一下
            new JSMpeg.Player('ws://${serverIP}:${forwardPort}/rtsp?url=' + btoa(rtsp), {
            canvas: document.getElementById('canvas-1')
            })
        }
    </script>
    </html>
    `;
}

// 发送包含HTML内容的响应
function sendHtmlResponse(res, htmlContent) {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.write(htmlContent);
    res.end();
}

// 发送包含HTML内容的响应
function sendHtmlContent(res, htmlContent) {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.write(htmlContent);
    res.end();
}

// 发送HTML文件
function sendHtmlFile(res, filename) {
    fs.readFile(filename, 'utf8', (err, data) => {
        if (err) {
            sendNotFound(res);
        } else {
            sendHtmlContent(res, data);
        }
    });
}

// 发送文件
function sendFile(res, filename) {
    fs.readFile(filename, (err, data) => {
        if (err) {
            sendNotFound(res);
        } else {
            res.writeHead(200);
            res.write(data);
            res.end();
        }
    });
}

// 发送 404 Not Found 响应
function sendNotFound(res) {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.write('404 Not Found');
    res.end();
}

function serveVideo(res, filePath) {
    const stat = fs.statSync(filePath);
    const fileSize = stat.size;

    // If the request doesn't contain the 'Range' header, serve the whole video
    const head = {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
    };

    res.writeHead(200, head);
    fs.createReadStream(filePath).pipe(res);
}
