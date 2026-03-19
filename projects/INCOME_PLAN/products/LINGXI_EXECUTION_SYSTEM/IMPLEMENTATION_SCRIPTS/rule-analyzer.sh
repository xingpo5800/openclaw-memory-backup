#!/bin/bash
# 规则分析器

# 规则优先级矩阵
declare -A RULE_PRIORITY
RULE_PRIORITY["system-rules.md"]=4
RULE_PRIORITY["execution-priority.md"]=3
RULE_PRIORITY["token-saver.md"]=2
RULE_PRIORITY["communication.md"]=1
RULE_PRIORITY["animation-script.md"]=1

# 冲突解决函数
resolve_conflict() {
    local rule1="$1"
    local rule2="$2"
    
    echo "[冲突检测] 发现规则冲突：$rule1 vs $rule2"
    
    local priority1=${RULE_PRIORITY[$rule1]}
    local priority2=${RULE_PRIORITY[$rule2]}
    
    if [[ -z "$priority1" ]]; then
        priority1=1
    fi
    
    if [[ -z "$priority2" ]]; then
        priority2=1
    fi
    
    echo "[优先级] $rule1: $priority1, $rule2: $priority2"
    
    if [[ $priority1 -gt $priority2 ]]; then
        echo "[决策] 优先执行 $rule1"
        echo "$rule1"
    elif [[ $priority2 -gt $priority1 ]]; then
        echo "[决策] 优先执行 $rule2"
        echo "$rule2"
    else
        echo "[决策] 优先级相同，建议人工决策"
        echo "manual"
    fi
}

# 风险评估函数
assess_risk() {
    local rule_name="$1"
    local change_type="$2"
    
    echo "[风险评估] 规则：$rule_name，变更类型：$change_type"
    
    case "$change_type" in
        "modify")
            if [[ "$rule_name" == "system-rules.md" ]]; then
                echo "[风险] 高风险：修改系统核心规则"
                return 3
            elif [[ "$rule_name" == "execution-priority.md" ]]; then
                echo "[风险] 中高风险：修改执行核心规则"
                return 2
            else
                echo "[风险] 低风险：修改辅助规则"
                return 1
            fi
            ;;
        "delete")
            echo "[风险] 极高风险：删除规则文件"
            return 4
            ;;
        "create")
            echo "[风险] 低风险：创建新规则"
            return 1
            ;;
        *)
            echo "[风险] 中等风险：未知变更类型"
            return 2
            ;;
    esac
}

# 使用方法
usage() {
    echo "使用方法: $0 [command] [arguments]"
    echo "命令："
    echo "  conflict <rule1> <rule2>  - 检测并解决规则冲突"
    echo "  risk <rule_name> <change_type> - 评估规则变更风险"
    echo "  priority <rule_name> - 查询规则优先级"
}

# 主程序
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    case "$1" in
        "conflict")
            if [[ $# -ne 3 ]]; then
                echo "错误：conflict命令需要两个规则文件名"
                usage
                exit 1
            fi
            resolve_conflict "$2" "$3"
            ;;
        "risk")
            if [[ $# -ne 3 ]]; then
                echo "错误：risk命令需要规则名和变更类型"
                usage
                exit 1
            fi
            assess_risk "$2" "$3"
            ;;
        "priority")
            if [[ $# -ne 2 ]]; then
                echo "错误：priority命令需要一个规则文件名"
                usage
                exit 1
            fi
            local priority=${RULE_PRIORITY[$2]}
            if [[ -z "$priority" ]]; then
                priority=1
            fi
            echo "[优先级] $2: $priority"
            ;;
        *)
            echo "错误：未知命令 '$1'"
            usage
            exit 1
            ;;
    esac
}

main "$@"