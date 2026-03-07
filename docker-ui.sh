#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LOCAL_BIN="$SCRIPT_DIR/.bin"

TITLE="Docker Manager Pro"
BACKTITLE="Docker Ops Console"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed or not in PATH"
  exit 1
fi

GUM_BIN=""
if [[ -x "$LOCAL_BIN/gum" ]]; then
  GUM_BIN="$LOCAL_BIN/gum"
elif command -v gum >/dev/null 2>&1; then
  GUM_BIN="$(command -v gum)"
fi

USE_GUM=false
if [[ -n "$GUM_BIN" ]]; then
  USE_GUM=true
fi

install_gum_local() {
  if [[ -n "$GUM_BIN" ]]; then
    return 0
  fi
  if ! command -v go >/dev/null 2>&1; then
    echo "Go is not installed; cannot auto-install gum locally."
    return 1
  fi

  mkdir -p "$LOCAL_BIN"
  echo "Installing gum locally at $LOCAL_BIN/gum ..."
  if GOBIN="$LOCAL_BIN" go install github.com/charmbracelet/gum@latest; then
    GUM_BIN="$LOCAL_BIN/gum"
    USE_GUM=true
    return 0
  fi

  echo "gum installation failed."
  return 1
}

if [[ "${1:-}" == "--install-gum" ]]; then
  install_gum_local || true
  exit 0
fi

if ! $USE_GUM && ! command -v whiptail >/dev/null 2>&1; then
  cat <<'MSG'
Neither gum nor whiptail is available.
Install gum with:
  ./docker-ui.sh --install-gum
MSG
  exit 1
fi

msg() {
  local text="$1"
  if $USE_GUM; then
    "$GUM_BIN" style --border rounded --padding "1 2" --foreground 212 --border-foreground 63 "$text"
    read -r -p "Press Enter to continue..." _
  else
    whiptail --title "$TITLE" --msgbox "$text" 16 80
  fi
}

confirm() {
  local text="$1"
  if $USE_GUM; then
    "$GUM_BIN" confirm "$text"
  else
    whiptail --title "$TITLE" --yesno "$text" 10 70
  fi
}

show_cmd_output() {
  local tmp
  tmp=$(mktemp)

  if ! "$@" >"$tmp" 2>&1; then
    if [[ -s "$tmp" ]]; then
      printf "Command failed:\n%s\n\n" "$*" | cat - "$tmp" >"${tmp}.err"
      mv "${tmp}.err" "$tmp"
    else
      printf "Command failed:\n%s\n" "$*" >"$tmp"
    fi
  elif [[ ! -s "$tmp" ]]; then
    echo "No output" >"$tmp"
  fi

  if $USE_GUM; then
    "$GUM_BIN" pager <"$tmp"
  else
    whiptail --title "$TITLE" --scrolltext --textbox "$tmp" 30 115
  fi

  rm -f "$tmp"
}

get_summary() {
  local running all images networks volumes
  running=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
  all=$(docker ps -aq 2>/dev/null | wc -l | tr -d ' ')
  images=$(docker images -q 2>/dev/null | sort -u | wc -l | tr -d ' ')
  networks=$(docker network ls -q 2>/dev/null | wc -l | tr -d ' ')
  volumes=$(docker volume ls -q 2>/dev/null | wc -l | tr -d ' ')

  cat <<EOF_SUM
Docker Snapshot
- Containers running : $running
- Containers total   : $all
- Images             : $images
- Networks           : $networks
- Volumes            : $volumes
EOF_SUM
}

show_dashboard() {
  local tmp
  tmp=$(mktemp)
  {
    get_summary
    echo
    echo "Disk Usage"
    echo
    docker system df 2>/dev/null || echo "Unable to query docker system usage."
  } >"$tmp"

  if $USE_GUM; then
    "$GUM_BIN" style --border rounded --padding "1 2" --foreground 86 --border-foreground 63 "Dashboard"
    "$GUM_BIN" pager <"$tmp"
  else
    whiptail --title "$TITLE - Dashboard" --scrolltext --textbox "$tmp" 30 115
  fi

  rm -f "$tmp"
}

# ---------- Selection helpers ----------

choose_from_lines_single() {
  local header="$1"
  shift
  local lines=("$@")
  [[ ${#lines[@]} -eq 0 ]] && return 1

  if $USE_GUM; then
    local selected
    selected=$(printf '%s\n' "${lines[@]}" | "$GUM_BIN" filter --height 20 --prompt "> " --placeholder "$header") || return 1
    printf '%s\n' "$selected"
  else
    local opts=()
    local line key desc
    for line in "${lines[@]}"; do
      key="${line%%|*}"
      desc="${line#*|}"
      opts+=("$key" "$desc")
    done
    whiptail --title "$TITLE" --menu "$header" 24 120 14 "${opts[@]}" 3>&1 1>&2 2>&3
  fi
}

choose_from_lines_multi() {
  local header="$1"
  shift
  local lines=("$@")
  [[ ${#lines[@]} -eq 0 ]] && return 1

  if $USE_GUM; then
    printf '%s\n' "${lines[@]}" | "$GUM_BIN" choose --no-limit --height 20 --header "$header"
  else
    local opts=()
    local line key desc
    for line in "${lines[@]}"; do
      key="${line%%|*}"
      desc="${line#*|}"
      opts+=("$key" "$desc" OFF)
    done
    whiptail --title "$TITLE" --checklist "$header" 26 120 16 "${opts[@]}" 3>&1 1>&2 2>&3 | tr -d '"'
  fi
}

container_lines() {
  local include_all="${1:-true}"
  local args=(--format '{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}')
  if [[ "$include_all" == "true" ]]; then
    args=(-a "${args[@]}")
  fi
  docker ps "${args[@]}" | awk -F'|' '{printf "%s|%s | %s | %s\n", $1,$2,$3,$4}'
}

image_lines() {
  docker images --format '{{.ID}}|{{.Repository}}:{{.Tag}}|{{.Size}}|{{.CreatedSince}}' | awk -F'|' '{printf "%s|%s | %s | %s\n", $1,$2,$3,$4}'
}

extract_id_from_line() {
  local line="$1"
  echo "${line%%|*}"
}

extract_ids_from_multi() {
  local raw="$1"
  local out=()

  if $USE_GUM; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      out+=("$(extract_id_from_line "$line")")
    done <<<"$raw"
  else
    mapfile -t out < <(xargs -n1 <<<"$raw")
  fi

  printf '%s\n' "${out[@]}"
}

menu_pick() {
  local header="$1"
  shift
  local items=("$@")

  if $USE_GUM; then
    "$GUM_BIN" choose --header "$header" "${items[@]}"
  else
    local opts=()
    local i=1
    local item
    for item in "${items[@]}"; do
      opts+=("$i" "$item")
      i=$((i + 1))
    done
    local choice
    choice=$(whiptail --title "$TITLE" --backtitle "$BACKTITLE" --menu "$header" 22 88 14 "${opts[@]}" 3>&1 1>&2 2>&3) || return 1
    echo "${items[$((choice - 1))]}"
  fi
}

input_number() {
  local prompt="$1"
  local default_val="$2"

  if $USE_GUM; then
    "$GUM_BIN" input --value "$default_val" --placeholder "$prompt"
  else
    whiptail --inputbox "$prompt" 10 60 "$default_val" 3>&1 1>&2 2>&3
  fi
}

# ---------- Menus ----------

container_menu() {
  while true; do
    local action
    action=$(menu_pick "Container Actions" \
      "List running" \
      "List all" \
      "Start container" \
      "Stop container" \
      "Restart container" \
      "View logs" \
      "Inspect container" \
      "Delete containers" \
      "Back") || break

    case "$action" in
      "List running") show_cmd_output docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' ;;
      "List all") show_cmd_output docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' ;;
      "Start container"|"Stop container"|"Restart container"|"View logs"|"Inspect container")
        mapfile -t lines < <(container_lines true)
        if [[ ${#lines[@]} -eq 0 ]]; then
          msg "No containers found."
          continue
        fi

        local selected id
        selected=$(choose_from_lines_single "Search and select a container" "${lines[@]}") || continue
        id=$(extract_id_from_line "$selected")

        case "$action" in
          "Start container") show_cmd_output docker start "$id" ;;
          "Stop container") show_cmd_output docker stop "$id" ;;
          "Restart container") show_cmd_output docker restart "$id" ;;
          "Inspect container") show_cmd_output docker inspect "$id" ;;
          "View logs")
            local n
            n=$(input_number "How many log lines?" "200") || continue
            [[ "$n" =~ ^[0-9]+$ ]] || n=200
            show_cmd_output docker logs --tail "$n" "$id"
            ;;
        esac
        ;;
      "Delete containers")
        mapfile -t lines < <(container_lines true)
        if [[ ${#lines[@]} -eq 0 ]]; then
          msg "No containers found."
          continue
        fi

        local picked raw_ids
        picked=$(choose_from_lines_multi "Select containers to delete" "${lines[@]}") || continue
        [[ -z "$picked" ]] && continue

        mapfile -t raw_ids < <(extract_ids_from_multi "$picked")
        [[ ${#raw_ids[@]} -eq 0 ]] && continue

        if confirm "Delete ${#raw_ids[@]} container(s)? This cannot be undone."; then
          show_cmd_output docker rm "${raw_ids[@]}"
        fi
        ;;
      "Back") break ;;
    esac
  done
}

image_menu() {
  while true; do
    local action
    action=$(menu_pick "Image Actions" \
      "List images" \
      "Delete images" \
      "Prune dangling" \
      "Prune unused" \
      "Back") || break

    case "$action" in
      "List images") show_cmd_output docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}' ;;
      "Delete images")
        mapfile -t lines < <(image_lines)
        if [[ ${#lines[@]} -eq 0 ]]; then
          msg "No images found."
          continue
        fi

        local picked raw_ids
        picked=$(choose_from_lines_multi "Select images to delete" "${lines[@]}") || continue
        [[ -z "$picked" ]] && continue

        mapfile -t raw_ids < <(extract_ids_from_multi "$picked")
        [[ ${#raw_ids[@]} -eq 0 ]] && continue

        if confirm "Delete ${#raw_ids[@]} image(s)?"; then
          show_cmd_output docker rmi "${raw_ids[@]}"
        fi
        ;;
      "Prune dangling")
        if confirm "Prune dangling images?"; then
          show_cmd_output docker image prune -f
        fi
        ;;
      "Prune unused")
        if confirm "Prune all unused images?"; then
          show_cmd_output docker image prune -a -f
        fi
        ;;
      "Back") break ;;
    esac
  done
}

system_menu() {
  while true; do
    local action
    action=$(menu_pick "System Actions" \
      "Dashboard" \
      "System info" \
      "Disk usage" \
      "Prune stopped containers" \
      "Back") || break

    case "$action" in
      "Dashboard") show_dashboard ;;
      "System info") show_cmd_output docker info ;;
      "Disk usage") show_cmd_output docker system df ;;
      "Prune stopped containers")
        if confirm "Delete all stopped containers?"; then
          show_cmd_output docker container prune -f
        fi
        ;;
      "Back") break ;;
    esac
  done
}

welcome() {
  if $USE_GUM; then
    "$GUM_BIN" style --border rounded --padding "1 2" --margin "1 0" \
      --foreground 86 --border-foreground 45 --bold \
      $'Docker Manager Pro\nFast, interactive container and image operations'
    "$GUM_BIN" style --foreground 245 "Backend: gum ($GUM_BIN)"
  else
    msg "Running in classic mode (whiptail).\nTip: run './docker-ui.sh --install-gum' for an enhanced UI."
  fi
}

main() {
  welcome
  while true; do
    local action
    action=$(menu_pick "Main Menu" \
      "Dashboard" \
      "Containers" \
      "Images" \
      "System" \
      "Install gum locally" \
      "Quit") || break

    case "$action" in
      "Dashboard") show_dashboard ;;
      "Containers") container_menu ;;
      "Images") image_menu ;;
      "System") system_menu ;;
      "Install gum locally")
        if install_gum_local; then
          msg "gum installed successfully at $GUM_BIN. Restart the script for full gum mode."
        else
          msg "Unable to install gum automatically in this environment."
        fi
        ;;
      "Quit") break ;;
    esac
  done
}

main
