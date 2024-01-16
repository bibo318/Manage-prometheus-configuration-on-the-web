from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import os
import re
import validators
from datetime import timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'verysecretkey'
app.permanent_session_lifetime = timedelta(minutes=30) #Thoi gian session

USERS_FILE = 'users.txt'
PROMETHEUS_CONFIG_FILE = '/data/prometheus-config/prometheus.yml'

def is_valid_url(url):
    return validators.url(url)

def load_user_credentials():
    credentials = {}
    with open(USERS_FILE) as f:
        for line in f:
            # Sử dụng split với maxsplit=1 để tránh chia mật khẩu hash
            parts = line.strip().split(':', 1)
            if len(parts) == 2:
                username, password_hash = parts
                credentials[username] = password_hash
    return credentials

def is_valid_yaml(config_content):
    try:
        yaml.safe_load(config_content)
        return True, None
    except yaml.YAMLError as e:
        return False, f"Lỗi YAML tại dòng {e.problem_mark.line}: {e.problem}"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(username, password):
    users = load_user_credentials()
    return username in users and check_password_hash(users[username], password)

def read_yaml(yaml_file):
    with open(yaml_file, 'r') as file:
        return yaml.safe_load(file)

def write_yaml(yaml_file, data):
    with open(yaml_file, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

def add_config_to_yaml(yaml_file, new_config):
    current_data = read_yaml(yaml_file)
    if current_data is None:
        current_data = []

    # Thêm cấu hình mới vào dữ liệu hiện tại
    current_data.append(new_config)

    # Ghi lại dữ liệu đã cập nhật vào file YAML
    write_yaml(yaml_file, current_data)

        
def extract_job_names_and_paths(prometheus_config_file):
    with open(prometheus_config_file, 'r') as file:
        config = yaml.safe_load(file)
        job_paths = {}
        for job in config.get('scrape_configs', []):
            job_name = job.get('job_name', '')
            file_paths = job.get('file_sd_configs', [{}])[0].get('files', [])
            if file_paths:
                # Trích xuất đường dẫn, bao gồm "files_sd/"
                file_path_match = re.search(r'(files_sd/.+?\.yml)$', file_paths[0])
                if file_path_match:
                    full_path = '/data/prometheus-config/' + file_path_match.group(1)
                    job_paths[job_name] = full_path
                    logging.debug(f"Added job: {job_name}, YAML file path: {full_path}")
        return job_paths

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Đăng nhập không thành công. Vui lòng kiểm tra lại thông tin đăng nhập.'
    return render_template('login.html', error=error)
    

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Xóa phiên đăng nhập
    return redirect(url_for('login'))  # Chuyển hướng người dùng đến trang đăng nhập

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/add_config', methods=['GET', 'POST'])
def add_config():
    if not session.get('logged_in'):
        return redirect(url_for('login'))


    job_paths = extract_job_names_and_paths(PROMETHEUS_CONFIG_FILE)
    message = None

    if request.method == 'POST':
        selected_job = request.form.get('selected_job')
        config_file = job_paths.get(selected_job)
        targets_input = request.form.get('targets')

#Code chua xu ly url
#        if not targets_input or not all(is_valid_ip_port(target.strip()) for target in targets_input.split(',')):
#            message = "Mục tiêu không hợp lệ: Vui lòng nhập địa chỉ IP hợp lệ cùng với port."
#            return render_template('add_config.html', job_paths=job_paths, message=message)

        if not targets_input or not all(
           is_valid_ip_port(target.strip()) or is_valid_url(target.strip()) for target in targets_input.split(',')):
           message = "Mục tiêu không hợp lệ: Vui lòng nhập địa chỉ IP hợp lệ cùng với port hoặc URL hợp lệ."
           return render_template('add_config.html', job_paths=job_paths, message=message)


        # Xử lý các nhãn mặc định và tùy chỉnh
        labels = {}
        for label in ['hostgroup', 'service', 'tool', 'jobs']:
            label_value = request.form.get(f'{label}_value', '')
            label_custom = request.form.get(f'{label}_custom', '')
            if label_value:
                labels[label_value] = label_custom if label_custom else label_value

        # Xử lý các nhãn bổ sung từ trường động
        additional_names = request.form.getlist('additional_label_name[]')
        additional_values = request.form.getlist('additional_label_value[]')
        for name, value in zip(additional_names, additional_values):
            if name and value:
                labels[name] = value

        new_config = {
            'targets': [target.strip() for target in targets_input.split(',')],
            'labels': labels
        }

        add_config_to_yaml(config_file, new_config)
        message = "Đã thêm cấu hình thành công."
        return redirect(url_for('add_config')) 

    return render_template('add_config.html', job_paths=job_paths, message=message)


def is_valid_ip_port(target):
    return re.match(r'^\d{1,3}(\.\d{1,3}){3}:\d+$', target) is not None

import os
import logging

@app.route('/view_config', methods=['GET', 'POST'])
def view_config():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    job_paths = extract_job_names_and_paths(PROMETHEUS_CONFIG_FILE)
    selected_job = request.args.get('selected_job')  # Sử dụng request.args để lấy giá trị từ URL

    if selected_job:
        config_file = job_paths.get(selected_job)
        if config_file:
            try:
                with open(config_file, 'r') as file:
                    config_content = file.read()
                logging.debug(f"Loaded configuration for {selected_job}: {config_content}")
                return render_template('view_config.html', selected_job=selected_job, config_content=config_content, job_paths=job_paths)
            except Exception as e:
                logging.error(f"Error reading configuration for {selected_job}: {str(e)}")
                return render_template('view_config.html', selected_job=selected_job, config_content=None, job_paths=job_paths)
        else:
            logging.warning(f"Configuration file not found for {selected_job}")
            return render_template('view_config.html', selected_job=selected_job, config_content=None, job_paths=job_paths)

    return render_template('view_config.html', job_paths=job_paths, selected_job=None, config_content=None)

@app.route('/delete_config', methods=['GET', 'POST'])
def delete_config():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    job_paths = extract_job_names_and_paths(PROMETHEUS_CONFIG_FILE)
    selected_job = request.args.get('selected_job')

    if request.method == 'POST':
        edited_config_content = request.form.get('config_content')
        action = request.form.get('action')
        
        if action == 'Lưu Cấu Hình':
            is_valid, error_message = is_valid_yaml(edited_config_content)
            if not is_valid:
                return render_template('delete_config.html', selected_job=selected_job, config_content=edited_config_content, job_paths=job_paths, error_message=error_message)

            config_file = job_paths.get(selected_job)
            if config_file:
                try:
                    with open(config_file, 'w') as file:
                        file.write(edited_config_content)
                    logging.info(f"Configuration for {selected_job} has been updated.")
                    return render_template('delete_config.html', selected_job=selected_job, config_content=edited_config_content, job_paths=job_paths, success_message="Lưu thành công.")
                except Exception as e:
                    logging.error(f"Error updating configuration for {selected_job}: {str(e)}")
                    # Thêm xử lý lỗi tại đây

    if selected_job:
        config_file = job_paths.get(selected_job)
        if config_file:
            try:
                with open(config_file, 'r') as file:
                    config_content = file.read()
                return render_template('delete_config.html', selected_job=selected_job, config_content=config_content, job_paths=job_paths)
            except Exception as e:
                logging.error(f"Error reading configuration for {selected_job}: {str(e)}")
                # Thêm xử lý lỗi tại đây

    return render_template('delete_config.html', job_paths=job_paths, selected_job=None, config_content=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
#    app.run(debug=True)
