# 创建总结请求队列
import asyncio

from ..Config import config
from ..Model import detect_model

summary_queue = asyncio.Queue(maxsize=config.summary_max_queue_size)
_summary_worker_tasks = []
_max_workers = config.summary_queue_workers

model = detect_model()


async def _process_summary_worker():
    """处理总结请求队列的工作线程"""
    while True:
        # 从队列获取任务
        messages, prompt, future = await summary_queue.get()
        try:
            # 调用实际的总结方法
            result = await model.summary_history(messages, prompt)
            # 设置结果
            future.set_result(result)
        except Exception as e:
            # 如果发生错误，将异常传播回调用方
            future.set_exception(e)
        finally:
            # 标记任务完成
            summary_queue.task_done()


async def ensure_workers_running():
    """确保工作线程池正常运行"""
    global _summary_worker_tasks

    # 清理已完成的任务
    _summary_worker_tasks = [task for task in _summary_worker_tasks if not task.done()]

    # 创建新的工作线程，确保始终有指定数量的工作线程运行
    while len(_summary_worker_tasks) < _max_workers:
        task = asyncio.create_task(_process_summary_worker())
        _summary_worker_tasks.append(task)


async def queue_summary_request(messages: list[dict[str, str]], prompt: str) -> str:
    """将总结请求加入队列并等待结果"""
    # 确保工作线程池正常运行
    await ensure_workers_running()

    # 创建Future对象以获取结果
    future = asyncio.Future()

    # 将请求加入队列
    await summary_queue.put((messages, prompt, future))

    try:
        # 等待结果，设置超时时间
        return await asyncio.wait_for(future, timeout=config.summary_queue_timeout)
    except asyncio.TimeoutError:
        return "很抱歉，总结请求处理超时。请稍后再试。"
