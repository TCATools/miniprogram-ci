# -*- coding: utf-8 -*-
"""
miniprogram-ci: 微信小程序质量扫描工具
功能: 代码分析
用法: python3 main.py
"""

# 2024-01-19    kylinye    created

import copy
import os
import json
import subprocess

PACKAGE_SIZE_RULES = ["PACKAGE_SIZE_LIMIT"]
CONTAINS_OTHER_RULES = ["CONTAINS_OTHER_PKG_JS", "CONTAINS_OTHER_PKG_COMPONENTS"]
CONTAINS_UNUSED_RULES = ["CONTAINS_UNUSED_PLUGINS", "CONTAINS_UNUSED_COMPONENTS", "CONTAINS_UNUSED_CODES"]

class MiniprogramCI(object):
    def __get_task_params(self):
        """获取需要任务参数
        :return:
        """
        task_request_file = os.environ.get("TASK_REQUEST")
        # task_request_file = "task_request.json"
        with open(task_request_file, "r") as rf:
            task_request = json.load(rf)
        task_params = task_request["task_params"]

        return task_params

    def run(self):
        """
        :return:
        """
        # 代码目录直接从环境变量获取
        source_dir = os.environ.get("SOURCE_DIR", None)
        # source_dir = "/Users/kylinye/Workspace/UGit/tools/miniprogram-ci/wxapp-2048-master"
        work_dir = os.environ.get("RESULT_DIR", None)
        # work_dir = "workdir"
        print("[debug] source_dir: %s" % source_dir)
        # 其他参数从task_request.json文件获取
        task_params = self.__get_task_params()
        # 规则
        rules = task_params["rules"]

        result = []
        result_path = os.path.join(work_dir, "result.json")
        error_output = os.path.join(work_dir, "error.json")

        node_home = os.environ.get("NODE_HOME", None)
        cmd = [
            os.path.join(node_home, "bin", "miniprogram-ci"),
            "check-code-quality",
            "--appid",
            "wxsomeappid",
            "--private-key-path",
            "key.txt",
            "--project-path",
            source_dir,
            "--save-path",
            error_output
        ]

        scan_cmd = " ".join(cmd)
        print("[debug] cmd: %s" % scan_cmd)
        subproc = subprocess.Popen(scan_cmd, stderr=subprocess.STDOUT, shell=True)
        subproc.communicate()

        print("start data handle")
        # 数据处理
        try:
            with open(error_output, "r") as f:
                outputs_data = json.load(f)
        except:
            print("[error] 结果文件未找到或无法加载，返回空结果")
            with open(result_path, "w") as fp:
                json.dump(result, fp, indent=2)
            return

        if outputs_data:
            result = data_handle(outputs_data, rules)

        with open(result_path, "w") as fp:
            json.dump(result, fp, indent=2)

def data_handle(outputs_data:list, rules:list):
    result = []
    for item in outputs_data:
        rule_name = item['name']
        if rule_name not in rules:
            continue
        success = item['success']
        if success:
            continue
        text = item['text']
        url = item['docURL']
        detail = item.get('detail', None)
        detail_msg = "Detail: %s" % detail if detail else ""
        issue = {}
        issue['path'] = ".TCA_PROJECT_SUMMARY"
        issue['line'] = 0
        issue['column'] = 0
        issue['rule'] = rule_name
        issue['refs'] = []
        if rule_name in PACKAGE_SIZE_RULES:
            if isinstance(detail, dict):
                app_size = detail.get("__APP__", None)
                if app_size:
                    detail_msg = "Detail: APP Size = %.2fM" % (int(app_size)/1024/1024)
            issue['msg'] = "Text: %s\nDocURL: %s\n%s" % (text, url, detail_msg)
            result.append(issue)
            continue
        if rule_name in CONTAINS_OTHER_RULES:
            if isinstance(detail, dict):
                files = detail.get("files", [])
                comps = detail.get("comps", [])
                issue['msg'] = "Text: %s\nDocURL: %s" % (text, url)
                for f in files:
                    new_issue = copy.copy(issue)
                    new_issue['path'] = f
                    result.append(new_issue)
                for c in comps:
                    new_issue = copy.copy(issue)
                    new_issue['path'] = c
                    result.append(new_issue)
                continue
        if rule_name in CONTAINS_UNUSED_RULES:
            if isinstance(detail, list):
                issue['msg'] = "Text: %s\nDocURL: %s" % (text, url)
                for f in detail:
                    new_issue = copy.copy(issue)
                    new_issue['path'] = f
                    result.append(new_issue)
                continue
        issue['msg'] = "Text: %s\nDocURL: %s\n%s" % (text, url, detail_msg)
        result.append(issue)
    return result


if __name__ == "__main__":
    print("-- start run tool ...")
    MiniprogramCI().run()
    print("-- end ...")
