import os
import matplotlib.pyplot as plt
import pandas as pd
import base64
import io
from PIL import Image
from matplotlib import animation
from core.const import FPS


def save_frames_as_video(args, frames, filename):
    # path = os.path.join(args.savedir, args.scenario)
    path = args.savedir
    # filename = '/demo_{}_{}_{}.mp4'.format(args.scenario, ts, seed)
    if not os.path.isdir(path):
        os.makedirs(path)
    # Mess with this to change frame size
    fig, ax = plt.subplots(figsize=(frames[0].shape[1] / 144.0, frames[0].shape[0] / 144.0), dpi=144)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_position([0, 0, 1, 1])
    ax.axis('off')
    patch = ax.imshow(frames[0])

    def animate(i):
        patch.set_data(frames[i])

    writer = animation.FFMpegWriter(fps=FPS)
    anim = animation.FuncAnimation(fig, animate, frames=len(frames))
    anim.save(os.path.join(path, filename), writer=writer)

    print('Video saved at: {}'.format(os.path.join(path, filename)))


def save_evaluation_result(args, filename, result_df: pd.DataFrame):
    path = args.savedir
    # filename = '/demo_{}_{}_{}.mp4'.format(args.scenario, ts, seed)
    if not os.path.isdir(path):
        os.makedirs(path)
    result_df.to_excel(os.path.join(path, filename), index=False)

def save_base64_frames_as_video(args, encoded_frames, filename):
    path = args.savedir
    if not os.path.isdir(path):
        os.makedirs(path)

    # 解码第一帧以获取尺寸
    first_frame = decode_base64_image(encoded_frames[0])
    fig, ax = plt.subplots(figsize=(first_frame.width / 144.0, first_frame.height / 144.0), dpi=144)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_position([0, 0, 1, 1])
    ax.axis('off')
    
    im = ax.imshow(first_frame)

    def animate(i):
        frame = decode_base64_image(encoded_frames[i])
        im.set_array(frame)
        return [im]

    writer = animation.FFMpegWriter(fps=FPS)
    anim = animation.FuncAnimation(fig, animate, frames=len(encoded_frames), interval=1000/FPS)
    anim.save(os.path.join(path, filename), writer=writer)

    print('Video saved at: {}'.format(os.path.join(path, filename)))

def decode_base64_image(base64_string):
    # 移除数据URL前缀
    image_data = base64_string.split(',')[1]
    # 解码base64数据
    image_bytes = base64.b64decode(image_data)
    # 从字节数据创建PIL Image对象
    image = Image.open(io.BytesIO(image_bytes))
    return image