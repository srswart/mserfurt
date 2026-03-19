#!/usr/bin/env bash
#
# ARRIVE Hooks - Common Utilities
# Shared functions for all hook scripts
#

# Strict mode (but don't exit on error - hooks must be resilient)
set -uo pipefail

# ============================================================================
# Configuration
# ============================================================================

ARRIVE_CLI="${ARRIVE_CLI:-arrive}"
ARRIVE_HOOKS_DEBUG="${ARRIVE_HOOKS_DEBUG:-0}"

# ============================================================================
# Logging (to stderr, so it doesn't interfere with JSON output)
# ============================================================================

log_debug() {
    if [[ "$ARRIVE_HOOKS_DEBUG" == "1" ]]; then
        echo "[ARRIVE-HOOK DEBUG] $*" >&2
    fi
}

log_error() {
    echo "[ARRIVE-HOOK ERROR] $*" >&2
}

# ============================================================================
# JSON Helpers
# ============================================================================

# Check if jq is available
has_jq() {
    command -v jq &>/dev/null
}

# Parse JSON field (with fallback if jq not available)
json_get() {
    local json="$1"
    local field="$2"
    local default="${3:-}"
    
    if has_jq; then
        local value
        value=$(echo "$json" | jq -r ".$field // empty" 2>/dev/null)
        if [[ -n "$value" && "$value" != "null" ]]; then
            echo "$value"
        else
            echo "$default"
        fi
    else
        # Fallback: simple grep-based extraction (limited)
        echo "$default"
    fi
}

# Create notification JSON
json_notification() {
    local type="$1"  # info, warning, error
    local message="$2"
    
    if has_jq; then
        jq -n \
            --arg type "$type" \
            --arg msg "$message" \
            '{notifications: [{type: $type, message: $msg}]}'
    else
        # Fallback: manual JSON construction
        printf '{"notifications":[{"type":"%s","message":"%s"}]}' "$type" "$message"
    fi
}

# Create decision JSON
json_decision() {
    local decision="$1"  # allow, warn, block
    local message="$2"
    
    if has_jq; then
        jq -n \
            --arg dec "$decision" \
            --arg msg "$message" \
            '{decision: $dec, message: $msg}'
    else
        printf '{"decision":"%s","message":"%s"}' "$decision" "$message"
    fi
}

# Create empty/neutral response
json_empty() {
    echo '{}'
}

# ============================================================================
# ARRIVE CLI Wrappers
# ============================================================================

# Check if arrive CLI is available
has_arrive() {
    command -v "$ARRIVE_CLI" &>/dev/null
}

# Run arrive status and capture output
arrive_status() {
    if has_arrive; then
        "$ARRIVE_CLI" status 2>/dev/null
    else
        log_debug "arrive CLI not found"
        return 1
    fi
}

# Run arrive score and get JSON output
arrive_score_json() {
    if has_arrive; then
        "$ARRIVE_CLI" score --json 2>/dev/null
    else
        log_debug "arrive CLI not found"
        return 1
    fi
}

# Run arrive score and get plain output
arrive_score() {
    if has_arrive; then
        "$ARRIVE_CLI" score 2>/dev/null
    else
        log_debug "arrive CLI not found"
        return 1
    fi
}

# Run arrive check
arrive_check() {
    local strict="${1:-}"
    if has_arrive; then
        if [[ "$strict" == "--strict" ]]; then
            "$ARRIVE_CLI" check --strict 2>/dev/null
        else
            "$ARRIVE_CLI" check 2>/dev/null
        fi
    else
        log_debug "arrive CLI not found"
        return 1
    fi
}

# Run arrive draft
arrive_draft() {
    if has_arrive; then
        "$ARRIVE_CLI" draft 2>/dev/null
    else
        log_debug "arrive CLI not found"
        return 1
    fi
}

# Run arrive log
arrive_log() {
    local advance="$1"
    local commit_type="$2"
    local summary="$3"
    
    if has_arrive; then
        "$ARRIVE_CLI" log \
            --advance "$advance" \
            --commit-type "$commit_type" \
            --summary "$summary" 2>/dev/null
    else
        log_debug "arrive CLI not found"
        return 1
    fi
}

# ============================================================================
# Score Level Helpers
# ============================================================================

# Get score level from JSON score output
get_score_level() {
    local score_json="$1"
    json_get "$score_json" "level" "unknown"
}

# Get total score from JSON score output
get_score_total() {
    local score_json="$1"
    json_get "$score_json" "total" "0"
}

# Format score message based on level
format_score_message() {
    local total="$1"
    local level="$2"
    
    case "$level" in
        green)
            echo "Score: $total [GREEN] - looking good"
            ;;
        yellow)
            echo "Score: $total [YELLOW] - consider checkpoint"
            ;;
        red)
            echo "Score: $total [RED] - split recommended"
            ;;
        *)
            echo "Score: $total"
            ;;
    esac
}

# ============================================================================
# Advance Helpers
# ============================================================================

# Find existing advances in planned status
find_planned_advances() {
    local repo_root
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
    
    local arrive_dir="$repo_root/arrive/systems"
    if [[ ! -d "$arrive_dir" ]]; then
        return 1
    fi
    
    # Find all advance files with status: planned
    find "$arrive_dir" -name "ADV-*.md" -type f 2>/dev/null | while read -r file; do
        if grep -q "status: planned" "$file" 2>/dev/null; then
            echo "$file"
        fi
    done
}

# Get first planned advance (if any)
get_current_advance() {
    find_planned_advances | head -1
}

# Extract advance ID from file path
get_advance_id() {
    local file="$1"
    basename "$file" .md
}

# ============================================================================
# Git Helpers
# ============================================================================

# Check if we're in a git repo
in_git_repo() {
    git rev-parse --git-dir &>/dev/null
}

# Get list of changed files
get_changed_files() {
    if in_git_repo; then
        git diff --name-only 2>/dev/null
        git diff --name-only --cached 2>/dev/null
    fi | sort -u
}
