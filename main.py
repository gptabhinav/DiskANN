import sys
import subprocess
import yaml
import re
from copy import deepcopy

def substitute_vars(d, vars_dict):
    if isinstance(d, dict):
        return {k: substitute_vars(v, vars_dict) for k, v in d.items()}
    elif isinstance(d, list):
        return [substitute_vars(x, vars_dict) for x in d]
    elif isinstance(d, str):
        def repl(match):
            var = match.group(1)
            return str(vars_dict.get(var, match.group(0)))
        return re.sub(r"\$\{([^}]+)\}", repl, d)
    else:
        return d

def build_command(exe, args_list, config, program):
    cmd = [exe]
    if program == "fvecs_to_bin":
        cmd.append(str(config["data_type"]))
        cmd.append(str(config["input_file"]))
        cmd.append(str(config["output_file"]))
        return cmd
    for k in args_list:
        v = config.get(k)
        if v is None:
            continue
        if program == "search_memory_index" and k == "search_list":
            cmd.append("--search_list")
            # Only extend if v is a list
            if isinstance(v, list):
                cmd.extend(str(x) for x in v)
            else:
                # If v is a string, split by whitespace and filter out empty strings
                cmd.extend(str(x) for x in v.split() if x.strip())
        else:
            cmd.append(f"--{k}")
            cmd.append(str(v))
    return cmd

def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <program> <config.yaml>")
        sys.exit(1)
    program = sys.argv[1]
    config_file = sys.argv[2]

    with open(config_file) as f:
        all_configs = yaml.safe_load(f)

    global_cfg = all_configs.get("global", {})
    local_cfg = all_configs.get(program, {})
    exe = local_cfg.get("exe")
    args_list = local_cfg.get("args")

    if exe is None or args_list is None:
        print(f"Missing 'exe' or 'args' for {program} in YAML.")
        sys.exit(1)

    merged = deepcopy(global_cfg)
    merged.update(local_cfg)
    merged = substitute_vars(merged, merged)

    cmd = build_command(exe, args_list, merged, program)
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()