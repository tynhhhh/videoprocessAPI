import os, cv2, random, librosa, numpy as np
from moviepy.editor import VideoFileClip, ImageSequenceClip, AudioFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
from PIL import Image
from datetime import datetime
from joblib import Parallel, delayed
from pydub import AudioSegment

database_folder = os.path.join(os.getcwd(), "database")

def StoreInLocal():
    pass
#---------------------------------------------------------------------------------------------------------------------
class APIfunction():
    def __init__(self) -> None:
        self.database_folder = os.path.join(os.getcwd(), "database")
    @staticmethod
    def folderChecker(folder_path: str):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    def Cut(self, file: str, dur: int) -> list:
        database_path = os.path.join(self.database_folder, "SubVideos")
        self.folderChecker(database_path)
        try:
            if not file:
                return None
            _file = VideoFileClip(file)
            video_name = os.path.basename(file).split(".")[0]
            clip_duration = _file.duration
            num_subclips = int(clip_duration / dur)
            output_list = []
            for i in range(num_subclips):
                start = i * dur
                end = min((i + 1) * dur, clip_duration)
                output_name = f"cut_{video_name}_part{i+1}.mp4"
                sub_clip = _file.subclip(start, end)

                if i == num_subclips - 1:
                    remaining_duration = clip_duration - end
                    if remaining_duration > 0:
                        sub_clip = sub_clip.set_duration(sub_clip.duration + remaining_duration)

                output = os.path.join(database_path, output_name)
                sub_clip.write_videofile(output, codec='libx264')
                output_list.append(output)
            _file.close()
            return output_list
            
        except Exception as e:
            return e
#-----------------------------------------------------------------------------------------------------------------
    def logoGenerator(self, _file, position_x: int, position_y: int, logo, x_logo: int, y_logo: int):
        while True:
            ret, frame = _file.read()
            if not ret:
                break
            roi = frame[position_y:position_y + y_logo, position_x:position_x + x_logo]
            result = cv2.add(roi, logo)
            frame[position_y:position_y + y_logo, position_x:position_x + x_logo] = result
            yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def InsertLogo(self, file: str, logo: str, position: int = 1) -> str:
        database_path= os.path.join(self.database_folder, "LogoVideos")
        self.folderChecker(database_path)

        file_name = os.path.basename(file)
        valid_video_extensions = (".mp4", ".avi", ".mkv", ".mov")
        if not file_name.lower().endswith(valid_video_extensions):
            return 400, f"Make sure file {file} is a video!"
        if not Image.open(logo):
            return 400, f"Make sure file {file} is an image!"
        _file = cv2.VideoCapture(file)
        frame = _file.read()[1]
        x_logo, y_logo = 120, 80
        logo = cv2.resize(cv2.imread(logo), (x_logo, y_logo))
        y, x, _= frame.shape
        if x < y:
            x_vid_split, y_vid_split = x // 3, y // 2
        else:
            x_vid_split, y_vid_split = x // 2, y // 3
        position_x, position_y = (random.randint(x_vid_split*(position-1), x_vid_split*position), 
                                random.randint(y_vid_split*(position-4), y_vid_split*(position-3)))
        
        frames = self.logoGenerator(_file, position_x, position_y, logo, x_logo, y_logo)
        frames_list = list(frames)
        with ImageSequenceClip(frames_list, fps=_file.get(cv2.CAP_PROP_FPS)) as video:
            audio = AudioFileClip(file)
            video = video.set_audio(audio)
            output_name = f'logo_{file_name}'
            output = os.path.join(database_path, output_name)
            video.write_videofile(output, codec='libx264')
            return output
#---------------------------------------------------------------------------------------------------------------------
    def rsframeGenerator(self, _file, x_scale: int, y_scale: int, black_border, target_platform: int):
        frame_count= _file.get(cv2.CAP_PROP_FRAME_COUNT)
        count= 1
        print("Start changing frame resolution...")
        while True:
            ret, frame = _file.read()
            if not ret:
                break
            n_frame = cv2.resize(frame, (x_scale, y_scale))
            img_with_border = np.concatenate((black_border, n_frame, black_border), axis=target_platform)
            img_with_border_rgb = cv2.cvtColor(img_with_border, cv2.COLOR_BGR2RGB)
            print(f"{count}/{frame_count}: {count/frame_count*100:.2f}%")
            count += 1
            yield img_with_border_rgb
        print("Done changing frame resolution!")

    def ResolutionChanger(self, target_platform: int, files: list[str]):
        for file in files:
            if not file:
                return None
            _file = cv2.VideoCapture(file)
            x, y = int(_file.get(cv2.CAP_PROP_FRAME_WIDTH)), int(_file.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if target_platform == 1:  # For Windows
                x_target, y_target = 1920, 1080
            elif target_platform == 0:  # For mobile
                x_target, y_target = 720, 1280

            res_scale = min(x_target / x, y_target / y)
            x_scale, y_scale = int(x * res_scale), int(y * res_scale)

            if target_platform == 1:
                black_side = (x_target - x_scale) // 2
                black_border = np.zeros((y_scale, black_side, 3), dtype=np.uint8)
                if x_scale % 2 != 0:
                    x_scale -= 1
            elif target_platform == 0:
                black_side = (y_target - y_scale) // 2
                black_border = np.zeros((black_side, x_scale, 3), dtype=np.uint8)
                if y_scale % 2 != 0:
                    y_scale -= 1
            framesGenerator = self.rsframeGenerator(_file, x_scale, y_scale, black_border, target_platform)
            framesGenerator_list = list(framesGenerator)

            with ImageSequenceClip(framesGenerator_list, fps= _file.get(cv2.CAP_PROP_FPS)) as video:
                audio = AudioFileClip(file)
                video = video.set_audio(audio)
                yield video

    def videoConcat(self, target_platorm: int, files: list[str]):
        database_path= os.path.join(self.database_folder, "ConcatVideos")
        self.folderChecker(database_path)
        videos = self.ResolutionChanger(target_platorm, files)
        videos_list = list(videos)
        final_clip = concatenate_videoclips(videos_list, method="compose")
        now = datetime.now()
        output_name = now.strftime("%m%d%Y_%H%M%S")+".mp4"
        output = os.path.join(database_path, output_name)
        final_clip.write_videofile(output, codec='libx264')
        return output
#----------------------------------------------------------------------------------------------------------------------
    def process_frame_parallel(self, frame, blur_strength: int = 15):
        # Apply Gaussian blur to the frame
        blurred_frame = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)
        yield blurred_frame

    def BluringVideo(self, file: str, blur_strength: int = 15, num_jobs: int = -1) -> str:        
        _file = VideoFileClip(file)
        fps=_file.fps
        # Process frames in parallel
        processed_frames = Parallel(n_jobs=num_jobs, backend='threading')(
            delayed(self.process_frame_parallel)(frame, blur_strength) for frame in _file.iter_frames()
        )
        frame_list = [next(frame) for frame in processed_frames]
        with ImageSequenceClip(frame_list, fps=fps) as blurred_clip:
            audio = AudioFileClip(file)
            blurred_clip = blurred_clip.set_audio(audio)

            database_path = os.path.join(self.database_folder, "BlurVideos")
            self.folderChecker(database_path)
            file_name = os.path.basename(file)
            output = os.path.join(database_path, f"blur_{file_name}")
            blurred_clip.write_videofile(output, codec= "libx264")
            return output
#-----------------------------------------------------------------------------------------------------------------------
    def ChangingSpeed(self, file: str, speed_factor: float) -> str:
        _file = VideoFileClip(file)
        if not _file:
            return 0

        file_name = os.path.basename(file)
        fps = _file.fps
        # Speed up the video by a factor of 2
        speedup_clip = _file.fx(vfx.speedx, speed_factor)

        # Extract audio from the original video
        original_audio = _file.audio

        # Save the audio to a temporary WAV file
        temp_audio_name = 'temp_audio.wav'
        temp_audio_path = os.path.join(self.database_folder, temp_audio_name)

        original_audio.write_audiofile(temp_audio_path, codec='pcm_s16le', fps=original_audio.fps)

        # Load the audio using librosa
        song, fs = librosa.load(temp_audio_path)

        # Use librosa to stretch the audio without changing pitch
        song_2_times_faster = librosa.effects.time_stretch(song, rate=speed_factor)

        # Convert the NumPy array to an AudioSegment using pydub
        audio_segment = AudioSegment(
            np.array(np.int16(song_2_times_faster * 32767), dtype=np.int16).tobytes(),
            frame_rate=fs,
            sample_width=2,
            channels=1
        )
        audio_segment.export(temp_audio_path)

        audio = AudioFileClip(temp_audio_path)
        # Set the sped-up audio to the video _file
        final_clip = speedup_clip.set_audio(audio)

        # Export the final video
        database_path = os.path.join(self.database_folder, "speedupVideos")
        self.folderChecker(database_path)
        output = os.path.join(database_path, f"sp_{file_name}")
        final_clip.write_videofile(output, codec="libx264", audio_codec="aac", fps=_file.fps)

        # Close the video clips
        _file.close()
        speedup_clip.close()
        final_clip.close()
        os.remove(temp_audio_path)
        return output

if __name__ == "__main__":
    func = APIfunction()
    func.ChangingSpeed("testvideo.mp4",1.5)