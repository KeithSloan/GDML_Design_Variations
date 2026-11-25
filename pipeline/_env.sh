# Sourced by the pipeline's shell scripts.  Loads machine-specific settings
# from pipeline/local.env (not committed; see pipeline/local.env.example):
# KEY=VALUE lines, no quotes, # for comments.  A variable already set in the
# environment wins over local.env, so FREECAD=... on the command line still
# overrides it.
gdv_load_local_env() {
  local file="$1/pipeline/local.env" key val
  [ -f "$file" ] || return 0
  while IFS='=' read -r key val || [ -n "$key" ]; do
    key="${key// /}"
    case "$key" in ''|\#*) continue ;; esac
    if [ -z "${!key:-}" ]; then
      export "$key=$val"
    fi
  done < "$file"
}
