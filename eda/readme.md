git clone https://github.com/nghungvkck/Durian
cd eda

# tạo môi trường
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate


# cài đặt thư viện
pip install -r requirements.txt

# chạy
python main_app.py