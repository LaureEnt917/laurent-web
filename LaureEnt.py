from flask import Flask, render_template, request, redirect, url_for, flash, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import qrcode
import sys
import io

# Đặt encoding của stdout thành utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Khởi tạo Flask và cấu hình phân quyền
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Dùng để flash messages

# Cấu hình Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
client = gspread.authorize(CREDS)

# Truy cập vào Google Sheets
spreadsheet = client.open("LaureEntienne")  # Tên của Google Sheets
worksheet = spreadsheet.sheet1  # Sử dụng sheet đầu tiên

# Kiểm tra nếu là người quản lý
def is_admin():
    return session.get("user_email") == "taoaccdenuoioc@gmail.com"

# Lấy dữ liệu điểm từ Google Sheets
def get_points_data():
    records = worksheet.get_all_records()
    return records

# Lưu điểm và các thông tin vào Google Sheets
def save_data_to_sheet(name, class_name, points, link, avatar_url, quote, background_image):
    worksheet.append_row([name, class_name, points, link, avatar_url, quote, background_image])

# Kiểm tra URL có phải là nhóm Facebook hợp lệ không
def is_valid_facebook_group_link(link):
    allowed_group_url = "https://www.facebook.com/groups/9340534102694502"
    return allowed_group_url in link

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_points', methods=['POST'])
def add_points():
    name = request.form['name']
    class_name = request.form['class']
    points = request.form['points']
    link = request.form['link']
    avatar_url = request.form['avatar']
    quote = request.form['quote']
    background_image = request.form['background_image']  # Lấy URL ảnh nền từ form

    try:
        points = int(points)
    except ValueError:
        flash('Điểm phải là một số', 'error')
        return redirect(url_for('index'))

    if not is_valid_facebook_group_link(link):
        flash('Link phải là link của nhóm Facebook cụ thể!', 'error')
        return redirect(url_for('index'))

    # Lưu điểm và các thông tin vào Google Sheets
    save_data_to_sheet(name, class_name, points, link, avatar_url, quote, background_image)

    flash(f"Đã cộng {points} điểm cho {name}", 'success')

    return redirect(url_for('index'))

@app.route('/total_points')
def total_points():
    name = request.args.get('name')

    if not name:
        flash('Tên người dùng không hợp lệ', 'error')
        return redirect(url_for('index'))

    records = get_points_data()

    if not records:
        flash('Không có dữ liệu điểm!', 'error')
        return redirect(url_for('index'))

    total_points = 0
    found_user = False
    class_name = None
    avatar_url = None
    background_image = None
    quote = None

    for record in records:
        if record.get('name') and record.get('name').strip().lower() == name.strip().lower():
            found_user = True
            try:
                total_points += int(record['points'])
                class_name = record.get('class')
                avatar_url = record.get('avatar_url')
                background_image = record.get('background_image')
                quote = record.get('quote')
            except ValueError:
                flash(f"Điểm của {name} không hợp lệ: {record['points']}", 'error')
                return redirect(url_for('index'))

    if not found_user:
        flash(f"Không tìm thấy người dùng {name}", 'error')
        return redirect(url_for('index'))

    flash(f"Tổng điểm của {name} là {total_points}", 'info')

    return render_template('total_points.html', 
                           name=name, 
                           total_points=total_points, 
                           avatar_url=avatar_url, 
                           class_name=class_name, 
                           background_image_url=background_image,
                           quote=quote)

if __name__ == '__main__':
    app.run(debug=True)



