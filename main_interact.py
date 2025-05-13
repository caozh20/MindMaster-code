import argparse
import numpy as np
import random
import traceback
# from asgiref.wsgi import WsgiToAsgi
# import uvicorn

# np.random.seed(1234)
# random.seed(1234)

from utils.base import log
import globals
from website import create_app
from website.pipeline_utils_u2u import ScenarioRoom, GlobalRoomDict, read_user_tasks_data


# running configuration
parser = argparse.ArgumentParser(description=None)
parser.add_argument('-m', '--mode', default='u2u', choices=['u2u', 'u2m'], help='game mode default is \'u2m\'')
parser.add_argument('-f', '--fix_time_per_round', default=False, help='whether to fix the time of every round')
parser.add_argument('-t', '--control_test_mode', default=False, help='whether to conduct control test')
parser.add_argument('--host', default='0.0.0.0', help='host to run the server on')
parser.add_argument('--port', type=int, default=1200, help='port to run the server on')
# for uvicorn
parser.add_argument('--workers', type=int, default=4, help='number of worker processes')
parser.add_argument('--offline_experiment', default=True, action='store_true', help='whether to create and maintain specific room')
parser.add_argument('--prior_exp_path', default='./human_study/zero_pair.json', help='where to get specific data pair you want')


args = parser.parse_args()
log.info(args)


mode = args.mode
globals.global_user_task_dict = read_user_tasks_data()


if __name__ == '__main__':
    globals.global_rooms_dict = GlobalRoomDict(arg=args)
    globals.global_fix_time_per_round = args.fix_time_per_round

    if mode == 'u2u':
        app = create_app('u2u')
        # asgi_app = WsgiToAsgi(app)
    else:
        app = create_app('u2m')

    try:
        # normal server deployment
        app.run('0.0.0.0', debug=False, port=1200)
    except Exception as e:
        log.error(f"Unhandled exception: {str(e)}")
        log.error(traceback.format_exc())

    # unvicorn server deployment
    # uvicorn.run('main_interact:asgi_app', access_log=False,
    #             host=args.host, 
    #             port=args.port, 
    #             workers=args.workers)
