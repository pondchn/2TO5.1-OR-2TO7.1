import argparse
import os
import sys
import gc
import shutil
import subprocess
from pydub import AudioSegment

def delete_files_only(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # 删除文件或符号链接
            # 如果是目录则不处理
        except Exception as e:
            print(f"无法删除 {file_path}. 原因: {e}")

def update_progress(current_step, total_steps):
    done = int(100 * current_step / total_steps)
    progress_bar = f"{'=' * done}{' ' * (100 - done)}"
    print(f"\r混音进度: [{progress_bar}] {done}%:[{current_step}/{total_steps}]", end="")
    sys.stdout.flush()


def remix_channels(input_dir, output_file, channel_count, flac_flag=False):
    print(f"开始混音为 {channel_count}.1 通道，由 {input_dir} 到 {output_file}")

    total_steps = channel_count + 4  # 包括加载、调整采样率、创建静音、混音和导出
    current_step = 0

    # 定义声道文件列表
    channels = ["vocals", "bass", "drums", "guitar", "instrumental", "piano", "other"]
    mono_segments = []

    for channel in channels:
        filename = channel+ ".flac" if flac_flag else ".wav"
        channel_file = os.path.join(input_dir, filename)
        if os.path.isfile(channel_file):
            audio = AudioSegment.from_file(channel_file)
            mono_segments.append(audio)
        else:
            # 如果文件不存在，添加静音音频段作为占位符
            print(f"文件 {channel_file} 不存在，添加静音占位符")
            mono_segments.append(AudioSegment.silent(duration=0, frame_rate=48000))

    current_step += 1
    update_progress(current_step, total_steps)

    # 调整音频文件的采样率
    for i, segment in enumerate(mono_segments):
        mono_segments[i] = segment.set_frame_rate(48000)

    current_step += 1
    update_progress(current_step, total_steps)

    # 创建一个静音的声道音频对象（采样率 48kHz）
    silence = AudioSegment.silent(duration=len(mono_segments[0]), frame_rate=48000)

    current_step += 1
    update_progress(current_step, total_steps)

    # 混音为指定声道格式
    if channel_count == 5:
        # 中置声道：将 vocals 左右声道合并为单声道
        center_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[0].set_channels(1)  # vocals
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        # 低音声道：将 bass 左右声道合并为单声道
        lfe_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[1].set_channels(1)  # bass
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        # 左右主声道：使用 drums 的左右声道
        left_main = mono_segments[2].split_to_mono()[0].set_channels(1)  # drums 左声道
        right_main = mono_segments[2].split_to_mono()[1].set_channels(1)  # drums 右声道

        current_step += 1
        update_progress(current_step, total_steps)

        # 左右环绕声道：混合 piano、guitar、instrumental、other 和 vocals 的左右声道
        left_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[5].split_to_mono()[0].set_channels(1),  # piano
            mono_segments[3].split_to_mono()[0].set_channels(1),  # guitar
            mono_segments[4].split_to_mono()[0].set_channels(1),  # instrumental
            mono_segments[6].split_to_mono()[0].set_channels(1),  # other
            mono_segments[0].split_to_mono()[0].set_channels(1),  # vocals
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        right_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[5].split_to_mono()[1].set_channels(1),  # piano
            mono_segments[3].split_to_mono()[1].set_channels(1),  # guitar
            mono_segments[4].split_to_mono()[1].set_channels(1),  # instrumental
            mono_segments[6].split_to_mono()[1].set_channels(1),  # other
            mono_segments[0].split_to_mono()[1].set_channels(1),  # vocals
        ).set_channels(1)

        mono_segments = [
            left_main,  # 左前
            right_main,  # 右前
            center_channel,  # 中置
            lfe_channel,  # 低音
            left_surround,  # 左后
            right_surround,  # 右后
        ]

    elif channel_count == 7:
        # 中置声道：将 vocals 左右声道合并为单声道
        center_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[0].set_channels(1)  # vocals
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        # 低音声道：将 bass 左右声道合并为单声道
        lfe_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[1].set_channels(1)  # bass
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        # 左右主声道：使用 drums 的左右声道
        left_main = mono_segments[2].split_to_mono()[0].set_channels(1)  # drums 左声道
        right_main = mono_segments[2].split_to_mono()[1].set_channels(1)  # drums 右声道

        current_step += 1
        update_progress(current_step, total_steps)

        # 左右环绕声道：混合 piano、instrumental 和 vocals 的左右声道
        left_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[4].split_to_mono()[0].set_channels(1),  # instrumental
            mono_segments[5].split_to_mono()[0].set_channels(1),  # piano
            mono_segments[0].split_to_mono()[0].set_channels(1),  # vocals
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        right_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[4].split_to_mono()[1].set_channels(1),  # instrumental
            mono_segments[5].split_to_mono()[1].set_channels(1),  # piano
            mono_segments[0].split_to_mono()[1].set_channels(1),  # vocals
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        # 左后环绕和右后环绕：混合 guitar、other 和 vocals 的左右声道
        rear_left_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[3].split_to_mono()[0].set_channels(1),  # guitar
            mono_segments[6].split_to_mono()[0].set_channels(1),  # other
            mono_segments[4].split_to_mono()[0].set_channels(1),  # instrumental
            mono_segments[0].split_to_mono()[0].set_channels(1),  # vocals
        ).set_channels(1)

        current_step += 1
        update_progress(current_step, total_steps)

        rear_right_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[3].split_to_mono()[1].set_channels(1),  # guitar
            mono_segments[6].split_to_mono()[1].set_channels(1),  # other
            mono_segments[4].split_to_mono()[1].set_channels(1),  # instrumental
            mono_segments[0].split_to_mono()[1].set_channels(1),  # vocals
        ).set_channels(1)

        mono_segments = [
            left_main,  # 左前
            right_main,  # 右前
            center_channel,  # 中置
            lfe_channel,  # 低音
            left_surround,  # 左后
            right_surround,  # 右后
            rear_left_surround,  # 左后环绕
            rear_right_surround,  # 右后环绕
        ]

    current_step += 1
    update_progress(current_step, total_steps)

    mixed_audio = AudioSegment.from_mono_audiosegments(*mono_segments).set_channels(
        channel_count + 1
    )

    current_step += 1
    update_progress(current_step, total_steps)
    print("=======>",mixed_audio.channels, mixed_audio.frame_rate, mixed_audio.duration_seconds,len(mixed_audio.raw_data), len(mono_segments))
    # 导出为多声道音频文件
    try:
        mixed_audio.export(output_file, format="flac")
        print("Flac格式导出成功!")
    except Exception as e2:
        # 最后尝试: 导出为 WAV 格式
        print(f"FLAC 导出仍然失败: {e2}")
        print("尝试导出为 WAV 格式...")
        wav_file = output_file.replace('.flac', '.wav')
        mixed_audio.export(wav_file, format="wav")
        print(f"已导出为 WAV 格式: {wav_file}")
    gc.collect()


def parse_args():
    parser = argparse.ArgumentParser(
        description="立体声转5.1声道&7.1声道混音工具 v2.0 by 陈缘科技"
    )
    parser.add_argument(
        "--hardware",
        choices=["gpu", "cpu"],
        help="处理模式: gpu (3G以上显存推荐) 或 cpu",
        default="gpu"
    )
    parser.add_argument(
        "--mode",
        choices=["5.1", "7.1"],
        help="混音模式: 5.1 或 7.1",
        default="5.1"
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="输入音频文件所在目录",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="输出目录",
    )
    parser.add_argument(
        "--continue",
        action="store_true",
        dest="continue_processing",
        help="继续处理模式，跳过音频分离步骤直接混音（假定分离文件已存在）",
    )
    parser.add_argument(
        "--flac",
        action="store_true",
        dest="flac_file",
        help="导出为 FLAC 格式（默认导出为 WAV 格式）",
    )
    args = parser.parse_args()

    if not args.continue_processing and args.hardware is None:
        parser.error("--hardware 为必填项（使用 --continue 时可省略）")

    return args

def separate_audio(input_dir, hardware_choice, flac_flag=False):
    
    os.environ["TORCH_HOME"] = "./model"
    tempPath = "./temp/separate"
    if not os.path.exists(tempPath):
        os.mkdir(tempPath)

    print(f"分离音频目录为 {input_dir}.硬件： {hardware_choice}")
    if hardware_choice == "gpu":
        os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "0"
        args = [
            "python",
            "logic_bsroformer/inference.py",
            "--model_type",
            "bs_roformer",
            "--config_path",
            "logic_bsroformer/configs/logic_pro_config_v1.yaml",
            "--start_check_point",
            "logic_bsroformer/models/logic_roformer.pt",
            "--input_folder",
            os.path.dirname(input_dir),
            "--store_dir",
            tempPath,
            "--extract_instrumental",
        ]
    elif hardware_choice == "cpu":
        args = [
            "python",
            "logic_bsroformer/inference.py",
            "--model_type",
            "bs_roformer",
            "--config_path",
            "logic_bsroformer/configs/logic_pro_config_v1.yaml",
            "--start_check_point",
            "logic_bsroformer/models/logic_roformer.pt",
            "--input_folder",
            os.path.dirname(input_dir),
            "--store_dir",
            tempPath,
            "--extract_instrumental",
            "--force_cpu",
        ]
    else:
        args = []
    
    if flac_flag:
        args.append("--flac_file")

    if args:
        print(f"执行命令: {' '.join(args)}")
        result = subprocess.run(args, check=True)

def main():
    args = parse_args()

    input_directory = args.input_dir
    output_directory = args.output_dir

    if not os.path.isdir(input_directory):
        print(f"错误: 输入目录不存在: {input_directory}")
        sys.exit(1)

    os.makedirs(output_directory, exist_ok=True)

    if args.continue_processing:
        print("继续处理...")
    else:
        print("立体声转5.1声道&7.1声道混音工具 v2.0 by 陈缘科技")
        print()

    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        if not os.path.isfile(file_path):
            print(f"跳过子文件夹: {filename}")
            continue

        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, filename)

        # 删除临时目录中的复制音频文件
        delete_files_only(temp_dir)

        # 复制文件到临时目录
        shutil.copy(file_path, temp_file_path)
        fname,ext = os.path.splitext(filename)
        output_file = os.path.join(output_directory, fname + f"_{args.mode}.flac")
        if os.path.isfile(output_file):
            print(f"最终输出的音频文件已存在，跳过文件: {filename}")
            # delete_files_only(temp_dir)
            # separate_dir = os.path.join(temp_dir, "separate", fname)
            # if os.path.exists(separate_dir):
            #     delete_files_only(separate_dir)
            #     os.rmdir(separate_dir)
            #     print("已删除分离后的音频文件")
            continue

        print(f"正在处理文件: {filename}")

        isfull = False
        channels = ["vocals", "bass", "drums", "guitar", "instrumental", "piano", "other"]
        for sound in channels:
            dstfile = os.path.join(temp_dir, "separate", fname, sound + ".flac" if args.flac_file else ".wav")
            if os.path.isfile(dstfile):
                isfull = True
                print(f"{filename} 分离音频文件 {sound} 已存在，跳过分离")

        if not isfull and not args.continue_processing:
            separate_audio(temp_file_path, args.hardware, args.flac_file)

        output_file = os.path.join(output_directory, fname + f"_{args.mode}.flac")
        if not os.path.isfile(output_file):
            remix_channels(os.path.join(temp_dir, "separate", fname), output_file, int(args.mode.split(".")[0]), args.flac_file)
        else:
            print(f"\n{args.mode}混音已存在，请查看输出文件 {output_file}")

        delete_files_only(temp_dir)
        print("temp 中留有分离的音频文件，可自行删除，或者程序再次运行将自动清理")

        gc.collect()

    input("按任意键退出...")


if __name__ == "__main__":
    main()
