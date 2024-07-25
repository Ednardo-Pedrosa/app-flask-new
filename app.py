from flask import Flask, render_template, request, redirect, url_for
import paramiko
import re

app = Flask(__name__)

def execute_ssh_command(server_ip, port, username, password, command, root_username=None, root_password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    if username == 'root':
        ssh.connect(server_ip, port=port, username=root_username, password=root_password)
    else:
        ssh.connect(server_ip, port=port, username=username, password=password)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    result = stdout.read().decode()
    ssh.close()
    return result.strip()

def get_write_speed(server_ip, port, username, password, root_username, root_password):
    speeds = []
    for i in range(3):
        result = execute_ssh_command(server_ip, port, username, password, "dd if=/dev/zero of=testfile bs=1M count=1024 oflag=direct 2>&1 | tail -n 1 && rm testfile", root_username, root_password)
        print(f"Execução {i+1}: {result}")
        match = re.search(r'(\d+(\.\d+)?) MB/s', result)
        if match:
            speeds.append(float(match.group(1)))
    if speeds:
        average_speed = sum(speeds) / len(speeds)
        return f"Média de velocidade de escrita: {average_speed:.2f} MB/s"
    return "Erro ao calcular a velocidade de escrita"

def check_plan_requirements(storage, memory, plan):
    plans = {
        "plan1": {"storage": 21, "memory": 1.95},
        "plan2": {"storage": 21, "memory": 1}
    }
    
    selected_plan = plans[plan]
    storage_ok = storage >= selected_plan["storage"]
    memory_ok = memory >= selected_plan["memory"]
    
    return storage_ok, memory_ok

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        server_ip = request.form['server_ip']
        port = int(request.form['port'])
        username = request.form['username']
        password = request.form['password']
        root_username = request.form['root_username']
        root_password = request.form['root_password']
        plan = request.form['plan']

        storage_output = execute_ssh_command(server_ip, port, username, password, 'df -h', root_username, root_password)
        memory_output = execute_ssh_command(server_ip, port, username, password, 'awk \'/MemTotal/ {total=$2/1024/1024} /MemFree/ {free=$2/1024/1024} /MemAvailable/ {available=$2/1024/1024} /SwapTotal/ {swap_total=$2/1024/1024} /SwapFree/ {swap_free=$2/1024/1024} END {printf "Total: %.2f GB\\nEm uso: %.2f GB\\nDisponível: %.2f GB\\nSwap Total: %.2f GB\\nSwap Free: %.2f GB\\n", total, (total - free), available, swap_total, swap_free}\' /proc/meminfo', root_username, root_password)
        
        # Extract storage and memory information
        storage = float(re.search(r'/dev/.*?\s+(\d+)', storage_output).group(1))
        memory = float(re.search(r'Total: (\d+\.\d+)', memory_output).group(1))
        
        storage_ok, memory_ok = check_plan_requirements(storage, memory, plan)
        
        results = {
            'Armazenamento': storage_output,
            'Memória': memory_output,
            'Quantidade de CPU': execute_ssh_command(server_ip, port, username, password, 'nproc', root_username, root_password),
            'Taxa de Escrita do Disco': get_write_speed(server_ip, port, username, password, root_username, root_password),
            'Distribuição do Sistema Operacional': execute_ssh_command(server_ip, port, username, password, 'cat /etc/os-release', root_username, root_password),
            'Plano Selecionado': plan,
            'Atende ao Plano': f"Armazenamento: {'Sim' if storage_ok else 'Não'}, Memória: {'Sim' if memory_ok else 'Não'}"
        }

        return render_template('result.html', results=results)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')