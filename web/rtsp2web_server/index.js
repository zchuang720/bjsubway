
const RTSP2web = require('rtsp2web')

// 服务端长连接占据的端口号；端口号可以自定义
let port = 6102

new RTSP2web({
  port
})
