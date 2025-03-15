"""
通用状态机框架，包含状态管理、事件驱动、超时处理和上下文管理功能
"""

import threading
from enum import Enum
from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, List, Optional

_DEBUG = False

class EventType(Enum):
    TIMEOUT = "timeout"     # 超时事件类型
    NORMAL = "normal"       # 普通事件

@dataclass
class Event:
    type: EventType     # 事件类型
    name: str           # 事件名称
    data: Any = None    # 附加数据

class State:
    def __init__(self, name: str, is_end_state: bool = False):
        self.name = name                            # 状态名称
        self.is_end_state = is_end_state            # 是否为结束状态
        self.transitions: List[Transition] = []     # 状态转移规则列表
        self.timeout: Optional[float] = None        # 状态超时时间（秒）
        self.timeout_event: Optional[Event] = None  # 超时触发事件

    def add_transition(
        self,
        event_type: EventType,
        event_name: str,
        target: 'State',
        condition: Optional[Callable[[Dict], bool]] = None,
        action: Optional[Callable[[Dict], None]] = None
    ):
        """
        - event_type: 事件类型（TIMEOUT/NORMAL）
        - event_name: 事件名称标识符
        - target: 目标状态对象
        - condition: 可选的转移条件函数（接收context返回bool）
        - action: 转移发生时执行的动作函数（接收context）
        """
        self.transitions.append(Transition(
            event_type=event_type,
            event_name=event_name,
            target=target,
            condition=condition,
            action=action
        ))

    def add_timeout_transition(
        self,
        timeout: float,
        target: 'State',
        action: Optional[Callable[[Dict], None]] = None
    ):
        """
        - timeout: 超时时间（秒）
        - target: 超时后转移到的目标状态
        - action: 超时转移时执行的动作
        """
        self.timeout = timeout
        self.timeout_event = Event(EventType.TIMEOUT, "timeout")
        self.add_transition(
            event_type=EventType.TIMEOUT,
            event_name="timeout",
            target=target,
            action=action
        )

    def on_enter(self, context: Dict):
        pass

    def on_exit(self, context: Dict):
        pass

@dataclass
class Transition:
    event_type: EventType       # 触发事件类型
    event_name: str             # 事件名称
    target: State               # 目标状态
    condition: Optional[Callable[[Dict, Any], bool]] = None  # (context, event_data) => bool    # 转移条件
    action: Optional[Callable[[Dict, Any], None]] = None     # (context, event_data) => None    # 转移动作

class StateMachine:
    def __init__(self, initial_state: State, context: Optional[Dict] = None):
        self.current_state = initial_state              # 当前状态
        self.context = context or {}                    # 共享上下文数据
        self.timer: Optional[threading.Timer] = None    # 超时定时器
        self.lock = threading.Lock()                    # 线程安全锁
        self.running = False                            # 运行状态标识

    def start(self):
        with self.lock:
            if _DEBUG: print(f'线程 {threading.current_thread().name} 获得锁')
            if not self.running:
                self.running = True
                self._enter_state(self.current_state)
            if _DEBUG: print(f'线程 {threading.current_thread().name} 释放锁')

    def stop(self):
        with self.lock:
            if _DEBUG: print(f'线程 {threading.current_thread().name} 获得锁')
            self.running = False
            if self.timer:
                self.timer.cancel()
                self.timer = None
            if _DEBUG: print(f'线程 {threading.current_thread().name} 释放锁')
            if _DEBUG: print('状态机已停止')

    def handle_event(self, event: Event):
        with self.lock:
            if _DEBUG: print(f'线程 {threading.current_thread().name} 获得锁')
            for transition in self.current_state.transitions:
                condition_met = (
                    transition.condition is None or
                    transition.condition(self.context, event.data)
                )
                
                if (transition.event_type == event.type and
                    transition.event_name == event.name and
                    condition_met):
                    # 执行动作时传递event_data
                    if transition.action:
                        transition.action(self.context, event.data)
                    self._transition_to(transition.target)
                    break
            if _DEBUG: print(f'线程 {threading.current_thread().name} 释放锁')

            
        if self.current_state.is_end_state:
            self.stop()

    def _enter_state(self, state: State):
        state.on_enter(self.context)
        if state.timeout:
            self._start_timer(state.timeout)

    def _exit_state(self, state: State):
        state.on_exit(self.context)
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def _transition_to(self, target: State):
        if not self.running:
            return

        self._exit_state(self.current_state)
        self.current_state = target
        if _DEBUG: print(f'转移到状态 {self.current_state.name}')
        
        self._enter_state(self.current_state)

    def _start_timer(self, timeout: float):
        self.timer = threading.Timer(timeout, self._handle_timeout)
        self.timer.start()

    def _handle_timeout(self):
        self.handle_event(Event(EventType.TIMEOUT, "timeout"))


# 示例用法
if __name__ == "__main__":
    # 创建状态
    start_state = State("Start")
    processing_state = State("Processing")
    end_state = State("End", is_end_state=True)

    # 配置状态转移
    start_state.add_transition(
        event_type=EventType.NORMAL,
        event_name="start",
        target=processing_state,
        condition=lambda ctx, data: ctx.get("authorized", False),
        action=lambda ctx, data: print("Starting processing")
    )

    processing_state.add_timeout_transition(
        timeout=3.0,
        target=end_state,
        action=lambda ctx, data: print("Processing timeout")
    )

    # 初始化状态机
    context = {"authorized": True}
    sm = StateMachine(initial_state=start_state, context=context)

    # 运行状态机
    sm.start()

    # 发送事件
    sm.handle_event(Event(EventType.NORMAL, "start"))

    # 状态机会自动处理超时转移，或手动发送事件：
    # sm.handle_event(Event(EventType.NORMAL, "custom_event"))

