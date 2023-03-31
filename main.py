import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import requests
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = "5618373621:AAFsfQNYh5uopvKYZAWYWvWN4adZdmoH1C0"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Отправь мне фото или видео, и я наложу на них watermark.")

def process_photo_or_video(update: Update, context: CallbackContext):
    message = update.message
    file_id = None
    is_video = False

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
        is_video = True

    if file_id:
        file = context.bot.get_file(file_id)
        file_url = file.file_path

        if is_video:
            process_video(update, context, file_url)
        else:
            process_image(update, context, file_url)

def process_image(update: Update, context: CallbackContext, file_url: str):
    response = requests.get(file_url)
    img = Image.open(BytesIO(response.content)).convert("RGBA")

    watermark = create_watermark(img.size)
    img_with_watermark = Image.alpha_composite(img, watermark)
    img_with_watermark = img_with_watermark.convert("RGB")

    output = BytesIO()
    img_with_watermark.save(output, format="JPEG")
    output.seek(0)

    context.bot.send_photo(chat_id=update.message.chat_id, photo=output)

def process_video(update: Update, context: CallbackContext, file_url: str):
    response = requests.get(file_url)
    input_video = BytesIO(response.content)
    input_video.seek(0)

    video = VideoFileClip(input_video)
    watermark = create_watermark(video.size)

    watermark_frame = Image.alpha_composite(Image.new("RGBA", video.size, (0, 0, 0, 0)), watermark)
    watermark_frame = watermark_frame.convert("RGB")

    text_clip = ImageClip(watermark_frame).set_duration(video.duration)
    video_with_watermark = CompositeVideoClip([video, text_clip])

    output_video = BytesIO()
    video_with_watermark.write_videofile(output_video, codec="libx264", temp_audiofile="temp.m4a", remove_temp=True, audio_codec="aac")
    output_video.seek(0)

    context.bot.send_video(chat_id=update.message.chat_id, video=output_video)

def create_watermark(size):
    width, height = size
    font_size = int(height / 20)
    text = "ГОВОРИТСАРОВ"

    font = ImageFont.truetype("arial.ttf", font_size)
    text_width, text_height = font.getsize(text)

    watermark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, font=font, fill=(0, 0, 0, 76))
    return watermark

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo | Filters.video, process_photo_or_video))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()