from PIL import Image, ImageSequence
import os

def get_gif_dimensions(input_directory):
    gif_dimensions = []

    for filename in os.listdir(input_directory):
        if filename.endswith(".gif"):
            input_path = os.path.join(input_directory, filename)
            with Image.open(input_path) as img:
                width, height = img.size
                gif_dimensions.append((filename, width, height))
    
    return gif_dimensions

def print_gif_dimensions(gif_dimensions):
    for filename, width, height in gif_dimensions:
        print(f"{filename}: {width}x{height}")

# 可选：统计宽高情况
def analyze_dimensions(gif_dimensions):
    widths = [dim[1] for dim in gif_dimensions]
    heights = [dim[2] for dim in gif_dimensions]
    
    avg_width = sum(widths) / len(widths)
    avg_height = sum(heights) / len(heights)
    
    min_width = min(widths)
    max_width = max(widths)
    min_height = min(heights)
    max_height = max(heights)
    
    print(f"\n统计信息:")
    print(f"平均宽度: {avg_width:.2f}")
    print(f"平均高度: {avg_height:.2f}")
    print(f"最小宽度: {min_width}")
    print(f"最大宽度: {max_width}")
    print(f"最小高度: {min_height}")
    print(f"最大高度: {max_height}")


def resize_and_pad_gif(input_path, output_path, target_size):
    with Image.open(input_path) as img:
        frames = []
        # 获取帧速率（假设所有帧的持续时间相同）
        frame_duration = img.info['duration']
        for frame in ImageSequence.Iterator(img):
            frame = frame.convert("RGBA")
            original_width, original_height = frame.size

            # Calculate the new size preserving the aspect ratio
            aspect_ratio = original_width / original_height
            if original_width > original_height:
                new_width = target_size
                new_height = int(target_size / aspect_ratio)
            else:
                new_height = target_size
                new_width = int(target_size * aspect_ratio)
            
            # Resize the image
            resized_frame = frame.resize((new_width, new_height), Image.ANTIALIAS)

            # Create a new black background image
            # new_frame = resized_frame
            new_frame = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
            
            # Calculate position to paste the resized image
            paste_position = ((target_size - new_width) // 2, (target_size - new_height) // 2)
            
            # Paste the resized image onto the black background
            new_frame.paste(resized_frame, paste_position)
            frames.append(new_frame)

        # 创建一个纯黑帧
        # black_frame = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 255))

        # # 插入黑帧（2秒）
        # black_frames = [black_frame] * int(2000 / frame_duration)  # 2秒的黑帧

        # # 将黑帧添加到帧列表
        # frames.extend(black_frames)

        # Save the new GIF
        frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0, duration=img.info['duration'], disposal=2)

def process_gifs(input_directory, output_directory, target_size):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(input_directory):
        if filename.endswith(".gif"):
            input_path = os.path.join(input_directory, filename)
            output_path = os.path.join(output_directory, filename)
            resize_and_pad_gif(input_path, output_path, target_size)
            print(f"Processed {filename}")

input_directory = './assets/gif'  
# 替换为你的GIF存放目录
# gif_dimensions = get_gif_dimensions(input_directory)
# print_gif_dimensions(gif_dimensions)

output_directory = './assets/resize_gifs'  # 替换为你希望存放缩放后GIF的目录
target_size = 400  # 目标宽高

process_gifs(input_directory, output_directory, target_size)

# analyze_dimensions(gif_dimensions)