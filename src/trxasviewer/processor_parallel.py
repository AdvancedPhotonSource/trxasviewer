import time
from multiprocessing import Queue, Process, Manager
from queue import Empty
import logging
import os
from .trxas_dataset import TrXASDataset
import traceback
import numpy as np


CACHE_SIZE = 1024
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S')


class StreamDataReducer:
    def __init__(self, num_data=100, x0=None):
        self.x_sum = np.copy(x0)
        self.x_cnt = np.ones(x0)
        self.shape == x0.shape
    
    def add(self, x):
        if x.shape == self.shape:
            self.x_sum += x
            self.x_cnt += 1
        elif x.shape


def consumer_reduction(dsp_queue, flag_quit, cid):
    logger = logging.getLogger(f'[consumer_reduction_{cid}]')
    logger.info('initialized successfully')

    def process_job(**kwargs):
        t0 = time.perf_counter()
        try:
            fname = kwargs.pop('fname')
            dset = TrXASDataset(fname)
            result = dset.get_energy_vs_time(**kwargs)
            dsp_queue.put(result)
            tdiff = time.perf_counter() - t0
            short_name = os.path.basename(kwargs['fname'])
            logger.info(f"finished job: [{tdiff:0.3f}s] [{short_name}]")
        except Exception as e:
            logger.error(f'failed to process {kwargs["fname"]}')
            logger.error(traceback.format_exc())

    while True:
        if flag_quit.value:
            logger.info('receive quit command. quit now')
            break
        try:
            kwargs = dsp_queue.get(timeout=1)  # 1s
            cmd = kwargs.pop('cmd')
            if cmd == 'process':
                process_job(**kwargs)
            elif cmd == 'quit':
                logger.info('receive quit command. quit now')
                flag_quit.value = True
                break
        except Empty:
            pass
        except (KeyboardInterrupt, Exception) as e:
            logger.error('keyboard interrupt or other exception. quit now')
            logger.error(traceback.format_exc())
            flag_quit.value = True
            raise e


def consumer_normalization(job_queue, dsp_queue, cid, flag_quit):
    logger = logging.getLogger(f'[consumer_{cid}]')
    logger.info('initialized successfully')

    def process_job(**kwargs):
        t0 = time.perf_counter()
        try:
            fname = kwargs.pop('fname')
            dset = TrXASDataset(fname)
            result = dset.get_energy_vs_time(**kwargs)
            dsp_queue.put(result)
            tdiff = time.perf_counter() - t0
            short_name = os.path.basename(kwargs['fname'])
            logger.info(f"finished job: [{tdiff:0.3f}s] [{short_name}]")
        except Exception as e:
            logger.error(f'failed to process {kwargs["fname"]}')
            logger.error(traceback.format_exc())

    while True:
        if flag_quit.value:
            logger.info('receive quit command. quit now')
            break
        try:
            kwargs = job_queue.get(timeout=1)  # 1s
            cmd = kwargs.pop('cmd')
            if cmd == 'process':
                process_job(**kwargs)
            elif cmd == 'quit':
                logger.info('receive quit command. quit now')
                flag_quit.value = True
                break
        except Empty:
            pass
        except (KeyboardInterrupt, Exception) as e:
            logger.error('keyboard interrupt or other exception. quit now')
            logger.error(traceback.format_exc())
            flag_quit.value = True
            raise e


class ProcessingServer:
    def __init__(self, num_workers=2, proc_kwargs=None):
        manager = Manager()
        self.num_workers = num_workers
        self.status = None
        self.job_queue = Queue()  # Queue for jobs to be processed 
        self.dsp_queue = Queue()  # Queue for display 
        self.all_process = []

        # Use Manager's Value for num_jobs and flag_quit
        self.num_jobs = manager.Value('i', 0)
        self.flag_quit = manager.Value('b', False)

        # Use Manager for solver_kwargs and solver_kwargs_string
        self.solver_kwargs = manager.dict(proc_kwargs if proc_kwargs else {})

        # Initialize worker processes
        for idx in range(num_workers):
            p = Process(target=consumer_normalization,
                        args=(self.job_queue, self.dsp_queue, idx, self.flag_quit))
            p.start()
            self.all_process.append(p)

    def update_processing_parameters(self, new_kwargs):
        self.solver_kwargs.update(new_kwargs)

    def stop_server(self):
        self.flag_quit.value = True
        for p in self.all_process:
            p.join()

    def submit_jobs(self, flist):
        for f in flist:
            self.job_queue.put({'cmd': 'process',
                                'fname': f,
                                **dict(self.solver_kwargs)})


if __name__ == '__main__':
    pass
