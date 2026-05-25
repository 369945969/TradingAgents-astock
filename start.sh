#!/bin/bash

# TradingAgents 启动脚本
# 功能：检查进程状态，杀死已启动的进程，然后重新启动

set -e

# 配置项
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv_sandbox"
PID_FILE="${PROJECT_DIR}/tradingagents.pid"
LOG_FILE="${PROJECT_DIR}/tradingagents.log"
APP_MODE="${1:-cli}"  # 默认 CLI 模式

# Python 路径
if [[ -d "${VENV_DIR}" ]]; then
    PYTHON_BIN="${VENV_DIR}/bin/python"
else
    PYTHON_BIN="python3"
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印日志
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 检查进程是否存在
check_process() {
    if [[ -f "${PID_FILE}" ]]; then
        local pid=$(cat "${PID_FILE}")
        if kill -0 "${pid}" 2>/dev/null; then
            echo "${pid}"
            return 0
        else
            # PID 文件存在但进程不存在，删除 PID 文件
            rm -f "${PID_FILE}"
            return 1
        fi
    fi
    return 1
}

# 杀死进程
kill_process() {
    local pid=$(check_process)
    if [[ -n "${pid}" ]]; then
        log "${YELLOW}发现已运行的进程，PID: ${pid}，正在停止...${NC}"
        
        # 优雅停止
        kill "${pid}" 2>/dev/null
        
        # 等待进程结束
        local count=0
        while kill -0 "${pid}" 2>/dev/null; do
            sleep 1
            count=$((count + 1))
            if [[ ${count} -ge 10 ]]; then
                log "${RED}优雅停止超时，强制杀死进程...${NC}"
                kill -9 "${pid}" 2>/dev/null
                break
            fi
        done
        
        rm -f "${PID_FILE}"
        log "${GREEN}进程已停止${NC}"
    else
        log "没有运行中的进程"
    fi

    # 确保端口 8501 没有被占用
    local port_pid=$(lsof -ti:8501 2>/dev/null)
    if [[ -n "${port_pid}" ]]; then
        log "${YELLOW}端口 8501 被占用，PID: ${port_pid}，正在停止...${NC}"
        kill -9 ${port_pid} 2>/dev/null
        sleep 1
        log "${GREEN}端口 8501 已释放${NC}"
    fi
}

# 清理 Python 缓存
clean_pycache() {
    log "清理 Python 缓存..."
    find "${PROJECT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + >/dev/null 2>&1
    find "${PROJECT_DIR}" -type f -name "*.pyc" -delete >/dev/null 2>&1
    find "${PROJECT_DIR}" -type f -name "*.pyo" -delete >/dev/null 2>&1
    find "${PROJECT_DIR}" -type d -name ".cache" -exec rm -rf {} + >/dev/null 2>&1
    rm -rf ~/.streamlit/cache/ >/dev/null 2>&1
    log "${GREEN}缓存清理完成${NC}"
}

# 设置沙箱环境
setup_sandbox() {
    log "检查沙箱环境..."
    
    # 优先检测系统 Python
    local SYS_PYTHON=""
    if command -v python3 &>/dev/null; then
        SYS_PYTHON="python3"
    elif command -v python &>/dev/null; then
        SYS_PYTHON="python"
    fi
    
    if [[ -z "${SYS_PYTHON}" ]]; then
        log "${RED}未找到 Python，请先安装 Python 3${NC}"
        exit 1
    fi
    
    log "系统 Python: ${SYS_PYTHON} ($(${SYS_PYTHON} --version 2>&1))"
    
    # 尝试创建虚拟环境
    if [[ ! -d "${VENV_DIR}" ]]; then
        log "${YELLOW}创建虚拟环境...${NC}"
        if ${SYS_PYTHON} -m venv "${VENV_DIR}"; then
            log "${GREEN}虚拟环境创建成功${NC}"
        else
            log "${YELLOW}虚拟环境创建失败，使用系统 Python${NC}"
            PYTHON_BIN="${SYS_PYTHON}"
        fi
    fi
    
    # 确定 Python 路径
    if [[ -z "${PYTHON_BIN}" || ! -f "${PYTHON_BIN}" ]]; then
        PYTHON_BIN="${VENV_DIR}/bin/python"
    fi
    
    # 如果虚拟环境 Python 不存在，回退到系统 Python
    if [[ ! -f "${PYTHON_BIN}" ]]; then
        log "${YELLOW}虚拟环境 Python 不存在，回退到系统 Python${NC}"
        PYTHON_BIN="${SYS_PYTHON}"
    fi
    
    log "使用 Python: ${PYTHON_BIN}"
    
    log "升级 pip..."
    "${PYTHON_BIN}" -m pip install --upgrade pip >/dev/null 2>&1
    
    log "安装/更新依赖..."
    "${PYTHON_BIN}" -m pip install -e "${PROJECT_DIR}" >/dev/null 2>&1
    
    log "${GREEN}沙箱环境设置完成${NC}"
}

# 启动应用
start_application() {
    log "启动 TradingAgents (模式: ${APP_MODE})..."
    
    case "${APP_MODE}" in
        cli)
            log "启动 CLI 界面..."
            exec "${PYTHON_BIN}" -m cli.main
            ;;
        web)
            log "启动 Web 服务..."
            exec "${PYTHON_BIN}" -m web.launch
            ;;
        main)
            log "运行 main.py..."
            exec "${PYTHON_BIN}" "${PROJECT_DIR}/main.py"
            ;;
        *)
            log "${RED}未知模式: ${APP_MODE}${NC}"
            log "支持的模式: cli, web, main"
            exit 1
            ;;
    esac
}

# 主函数
main() {
    cd "${PROJECT_DIR}" || exit 1
    
    log "${GREEN}========== TradingAgents 启动脚本 ==========${NC}"
    
    # 0. 清理 Python 缓存（确保加载最新代码）
    clean_pycache
    
    # 1. 设置沙箱环境
    setup_sandbox
    
    # 2. 检查并杀死已运行的进程
    kill_process
    
    # 3. 启动应用
    log "启动应用..."
    local cmd
    case "${APP_MODE}" in
        cli)
            cmd="${PYTHON_BIN} -m cli.main"
            log "${GREEN}启动 CLI（前台交互模式）${NC}"
            log "${GREEN}============================================${NC}"
            ${cmd}
            exit $?
            ;;
        web)
            cmd="${PYTHON_BIN} -m streamlit run ${PROJECT_DIR}/web/app.py --server.headless true --server.port 8501"
            ;;
        main)
            cmd="${PYTHON_BIN} ${PROJECT_DIR}/main.py"
            ;;
    esac
    
    nohup bash -c "cd ${PROJECT_DIR} && ${cmd}" > "${LOG_FILE}" 2>&1 &
    local pid=$!
    echo "${pid}" > "${PID_FILE}"
    
    sleep 2
    
    if kill -0 "${pid}" 2>/dev/null; then
        log "${GREEN}应用启动成功，PID: ${pid}${NC}"
        log "${GREEN}日志文件: ${LOG_FILE}${NC}"
        log "${GREEN}============================================${NC}"
    else
        log "${RED}应用启动失败，请查看日志: ${LOG_FILE}${NC}"
        rm -f "${PID_FILE}"
        exit 1
    fi
}

# 显示帮助
usage() {
    echo "TradingAgents 启动脚本"
    echo ""
    echo "用法: $0 [模式]"
    echo ""
    echo "模式:"
    echo "  cli     - 启动 CLI 界面（默认）"
    echo "  web     - 启动 Web 服务"
    echo "  main    - 运行 main.py"
    echo ""
    echo "其他命令:"
    echo "  status  - 检查进程状态"
    echo "  stop    - 停止运行中的进程"
    echo "  restart - 重启应用（等同于执行 stop 然后 start）"
    echo ""
    echo "示例:"
    echo "  $0 web              # 启动 Web 服务"
    echo "  $0 cli              # 启动 CLI 界面"
    echo "  $0 status           # 查看状态"
    echo "  $0 stop             # 停止服务"
}

# 检查状态
status() {
    local pid=$(check_process)
    if [[ -n "${pid}" ]]; then
        echo -e "${GREEN}运行中${NC} - PID: ${pid}"
        echo "日志: ${LOG_FILE}"
    else
        echo -e "${RED}已停止${NC}"
    fi
}

# 停止服务
stop() {
    log "停止 TradingAgents..."
    kill_process
}

# 主入口
if [[ $# -eq 0 ]]; then
    main
    exit 0
fi

case "${1}" in
    status)
        status
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        main
        ;;
    cli|web|main)
        main
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        echo "未知命令: ${1}"
        usage
        exit 1
        ;;
esac
