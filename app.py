from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import boto3
from werkzeug.utils import secure_filename
from compress import convert_video
import base64
from zipfile import ZipFile
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS

# Load environment variables
S3_BUCKET = os.getenv('S3_BUCKET')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

# Amazon RDS configuration
RDS_USERNAME = os.getenv('RDS_USERNAME')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_HOSTNAME = os.getenv('RDS_HOSTNAME')
RDS_PORT = os.getenv('RDS_PORT', '3306')
RDS_DB_NAME = os.getenv('RDS_DB_NAME')

DATABASE_URI = f'mysql+mysqlconnector://{RDS_USERNAME}:{RDS_PASSWORD}@{RDS_HOSTNAME}:{RDS_PORT}/{RDS_DB_NAME}'
engine = create_engine(DATABASE_URI)
Base = declarative_base()

class User(Base):
    __tablename__ = 'new_data'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255), nullable=True)
    video = Column(String(255), nullable=True)
    image = Column(String(255), nullable=True)
    audio = Column(String(255), nullable=True)

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# AWS S3 configuration
s3_client = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)

@app.route('/data', methods=['POST'])
def upload_data():
    try:
        user_id = request.form.get('user_id')
        user_name = request.form.get('user_name')

        if 'video' not in request.files or 'image' not in request.files or 'audio' not in request.files:
            return jsonify({'error': 'Video, image, and audio files are required'}), 400

        video_file = request.files['video']
        image_file = request.files['image']
        audio_file = request.files['audio']

        if video_file.filename == '' or image_file.filename == '' or audio_file.filename == '':
            return jsonify({'error': 'All files (video, image, and audio) must be selected'}), 400

        video_filename = secure_filename(video_file.filename)
        image_filename = secure_filename(image_file.filename)
        audio_filename = secure_filename(audio_file.filename)

        # Save video to a temporary file for conversion
        temp_video_file = tempfile.NamedTemporaryFile(delete=False)
        video_file.save(temp_video_file.name)

        try:
            converted_video_data = convert_video(temp_video_file.name, size=5)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.unlink(temp_video_file.name)  # Remove temporary video file

        s3_video_key = f"{user_id}/video/{video_filename}"
        s3_image_key = f"{user_id}/image/{image_filename}"
        s3_audio_key = f"{user_id}/audio/{audio_filename}"

        # Upload converted video directly to S3
        s3_client.put_object(Bucket=S3_BUCKET, Key=s3_video_key, Body=converted_video_data)
        
        # Upload image and audio files directly to S3
        s3_client.upload_fileobj(image_file, S3_BUCKET, s3_image_key)
        s3_client.upload_fileobj(audio_file, S3_BUCKET, s3_audio_key)

        s3_video_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_video_key}"
        s3_image_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_image_key}"
        s3_audio_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_audio_key}"

        new_user = User(
            user_id=user_id,
            user_name=user_name,
            video=s3_video_url,
            image=s3_image_url,
            audio=s3_audio_url
        )
        session.add(new_user)
        session.commit()
        session.close()

        return jsonify({'message': 'Files uploaded and processed successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/watch/<int:user_id>', methods=['GET'])
def fetch_and_zip_media(user_id):
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            session.close()
            return jsonify({"error": "No media files found for the user"}), 404

        zip_filename = f'user_{user_id}.zip'
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, zip_filename)

            with open(zip_path, 'wb') as zip_file:
                with ZipFile(zip_file, 'w') as zipf:
                    for media_type in ['video', 'image', 'audio']:
                        media_url = getattr(user, media_type)
                        media_filename = os.path.basename(media_url)
                        temp_media_path = os.path.join(temp_dir, media_filename)
                        s3_client.download_file(S3_BUCKET, f"{user_id}/{media_type}/{media_filename}", temp_media_path)
                        zipf.write(temp_media_path, arcname=f"{media_type}/{media_filename}")

            with open(zip_path, 'rb') as f:
                zip_content = f.read()
                zip_base64 = base64.b64encode(zip_content).decode('utf-8')

        session.close()

        user_data = {
            'user_id': user_id,
            'user_name': user.user_name,
            'zip_file': zip_base64
        }

        return jsonify(user_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5002)
