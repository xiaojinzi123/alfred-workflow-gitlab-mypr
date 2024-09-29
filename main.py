""" curl --request GET \
  --header "PRIVATE-TOKEN: glpat-3SAVZnAxw1ZPGeGkBX8k" \
  --url "https://gitlab.example.com/api/v4/groups/29/approval_rules" """

import os
import json
import dataclasses
import pathlib
import argparse
import urllib
import urllib.parse

@dataclasses.dataclass
class CurrentUser:
    id: str
    name: str

@dataclasses.dataclass
class ProjectCache:
    id: str
    name: str
    description: str

@dataclasses.dataclass
class MergeRequest:
    id: str
    title: str
    webUrl: str
    authorId: str
    authorUserName: str | None
    projectId: str
    assigneeId: str | None
    assigneeName: str | None
    reviewerIdList: list[str]
    reviewerNameList: list[str]

def prJsonToMergeRequest(prJson: dict) -> MergeRequest:
    return MergeRequest(
        id = prJson.get("id"),
        title = prJson.get("title"),
        webUrl = prJson.get("web_url"),
        authorId = prJson.get("author").get("id"),
        authorUserName = prJson.get("author").get("username"),
        projectId=prJson.get("project_id"),
        assigneeId = prJson.get("assignee").get("id") if prJson.get("assignee") else "None",
        assigneeName = prJson.get("assignee").get("username") if prJson.get("assignee") else "None",
        reviewerIdList = [r.get("id") for r in prJson.get("reviewers")],
        reviewerNameList = [r.get("username") for r in prJson.get("reviewers")],
    )

if __name__ == '__main__':

    # 为了和 alfred 的输出分开
    isLog: bool = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--gitlabToken", type=str, default=None)
    parser.add_argument("--state", type=str, default=None)
    parser.add_argument("--search", type=str, default=None)
    parser.add_argument('--aboutSelf', action='store_true')
    parser.add_argument('--forTest', action='store_true')
    args = parser.parse_args()

    isLog = isLog or args.forTest
    state = args.state
    searchKey = args.search
    isAboutSelf = args.aboutSelf

    if isLog:
        print(f"state = {state}, searchKey = {searchKey}, isAboutSelf = {isAboutSelf}")
    
    if state != None:
        if state != "opened" and state != "closed" and state != "merged" and state != "all":
            print("state 参数错误")
            exit(1)

    gitlabToken = args.gitlabToken
    if gitlabToken == None or gitlabToken == "":
        gitlabToken = os.environ["gitlabToken"]
    
    if gitlabToken == None or gitlabToken == "":
        raise Exception("gitlabToken 不能为空")
    
    if isLog:
        print(f"gitlabToken = {gitlabToken}")

    # 获取我的信息的 curl 命令
    targetGetUserUrl = f"curl --request GET --header 'PRIVATE-TOKEN: {gitlabToken}' --url 'https://gitlab.vistring.com/api/v4/user'"

    # 获取当前用户的信息 CurrentUser
    currentUserJson = json.loads(os.popen(targetGetUserUrl).read())
    currentUser = CurrentUser(
        id=currentUserJson.get("id"),
        name=currentUserJson.get("name"),
    )

    if isLog:
        print(f"当前用户: {currentUser}")
    prCurlPrefix = f"curl --request GET --header 'PRIVATE-TOKEN: {gitlabToken}' --url "
    prUrlPrefix = f"https://gitlab.vistring.com/api/v4/merge_requests?"
    # 获取 PR 信息的 curl 命令
    targetPrUrl0 = prUrlPrefix
    targetPrUrl1 = prUrlPrefix
    targetPrUrl2 = prUrlPrefix
    queryParameterMap = {
        "scope": "all",
    }
    queryParameterMap0 = queryParameterMap.copy()
    queryParameterMap1 = queryParameterMap.copy()
    queryParameterMap2 = queryParameterMap.copy()

    if state != None:
        queryParameterMap0["state"] = state
        queryParameterMap1["state"] = state
        queryParameterMap2["state"] = state
    if searchKey != None:
        queryParameterMap0["search"] = searchKey
        # queryParameterMap0["in"] = "title,description"
        queryParameterMap1["search"] = searchKey
        # queryParameterMap1["in"] = "title,description"
        queryParameterMap2["search"] = searchKey
        # queryParameterMap2["in"] = "title,description"
    if isAboutSelf:
        queryParameterMap0["author_id"] = currentUser.id
        queryParameterMap1["assignee_id"] = currentUser.id
        queryParameterMap2["reviewer_id"] = currentUser.id
    targetPrUrl0 = f"{prCurlPrefix}'{targetPrUrl0}{urllib.parse.urlencode(queryParameterMap0)}'"
    targetPrUrl1 = f"{prCurlPrefix}'{targetPrUrl1}{urllib.parse.urlencode(queryParameterMap1)}'"
    targetPrUrl2 = f"{prCurlPrefix}'{targetPrUrl2}{urllib.parse.urlencode(queryParameterMap2)}'"
    targetProjectUrl = f"curl --request GET --header 'PRIVATE-TOKEN: {gitlabToken}' --url 'https://gitlab.vistring.com/api/v4/projects/'"

    if isLog:
        print(f"targetPrUrl0 = {targetPrUrl0}")
        print(f"targetPrUrl1 = {targetPrUrl1}")
        print(f"targetPrUrl2 = {targetPrUrl2}")
        print(f"targetProjectUrl = {targetProjectUrl}")

    # 获取当前目录
    currentPath = os.getcwd()
    if isLog:
        print(currentPath)
    
    targetCachedProjectJsonPath = pathlib.Path(f"{currentPath}/cacheData/projects.json")
    # 读取到 ProjectCache List
    projectCacheList: list[ProjectCache] = []
    if targetCachedProjectJsonPath.exists():
        # targetCachedProjectJsonPath 对应的文件 读取为 Text
        with open(targetCachedProjectJsonPath, 'r') as file:
            projectCacheListJson = json.loads(file.read())
            for p in projectCacheListJson:
                projectCacheList.append(
                    ProjectCache(
                        id=p.get("id"),
                        name=p.get("name"),
                        description=p.get("description"),
                    )
                )
    else:
        pass

    if isLog:
        print(projectCacheList)

    # if True:
        # exit(0)

    mergeRequestList: list[MergeRequest] = []
    # 执行 curl 命令获得结果
    # 将结果转换为 json 格式
    prListJson0 = json.loads(
        os.popen(targetPrUrl0).read()
    )
    prListJson1 = json.loads(
        os.popen(targetPrUrl1).read()
    )
    prListJson2 = json.loads(
        os.popen(targetPrUrl2).read()
    )

    # prListJson0 是否是 array
    if isinstance(prListJson0, list):
        # print("prListJson0 是 list")
        pass
    else:
        # print("prListJson0 不是 list")
        pass
    
    if isLog:
        # print(f"prListJson0: {prListJson0}")
        # print(f"prListJson1: {prListJson1}")
        # print(f"prListJson2: {prListJson2}")
        pass

    if isinstance(prListJson0, list):
        for pr in prListJson0:
            mergeRequestList.append(
                prJsonToMergeRequest(prJson=pr)
        )
    if isinstance(prListJson1, list):
        for pr in prListJson1:
            mergeRequestList.append(
                prJsonToMergeRequest(prJson=pr)
            )
    if isinstance(prListJson2, list):
        for pr in prListJson2:
            mergeRequestList.append(
                prJsonToMergeRequest(prJson=pr)
            )

    # 根据 id 去重
    mergeRequestList = list({pr.id: pr for pr in mergeRequestList}.values())

    if isLog:
        print()
        print(f"mergeRequestIdList: {[{pr.id: pr.title} for pr in mergeRequestList]}")
        print()
        print(f"mergeRequestList: {mergeRequestList}")
        print()

    # 从 mergeRequestList 中过滤出 authorId 是自己的 或者 assigneeId 或者 reviewerIdList 包含当前用户的 MergeRequest
    """ mergeRequestAboutMeList: list[MergeRequest] = []
    for pr in mergeRequestList:
        if currentUser.id == pr.authorId or currentUser.id == pr.assigneeId or currentUser.id in pr.reviewerIdList:
            mergeRequestAboutMeList.append(pr) """

    # 从 projectCacheList 过滤出在 mergeRequestList 不存在的 projectId List
    cachedProjectIdList = [p.id for p in projectCacheList]
    # 拿到没有缓存的 Project 信息
    noCachedProjectIdList = []
    for pr in mergeRequestList:
        if pr.projectId not in cachedProjectIdList:
            noCachedProjectIdList.append(pr.projectId)

    if isLog:
        print(f"noCachedProjectIdList: {noCachedProjectIdList}")

    # 从网络上更新没缓存的 Project 信息到 cachedProjectIdList 中
    for pId in noCachedProjectIdList:
        try:
            tempJson = json.loads(os.popen(f"{targetProjectUrl}{pId}").read())
            projectCacheList.append(
                ProjectCache(
                    id=tempJson.get("id"),
                    name=tempJson.get("name"),
                    description=tempJson.get("description"),
                )
            )
        except Exception as e:
            # ignore
            pass

    # 将 projectCacheList 写入到文件中
    with open(targetCachedProjectJsonPath, 'w') as file:
        file.write(json.dumps([dataclasses.asdict(p) for p in projectCacheList]))

    # 生命 alfred 的输出结果对象
    resultDict = {
        "items": [
        ],
    }

    # targetMergeRequestAboutAlfredList = mergeRequestAboutMeList
    targetMergeRequestAboutAlfredList = mergeRequestList

    if len(targetMergeRequestAboutAlfredList) == 0:
        resultDict["items"].append(
                {
                    "title": f"帅气逼人的 '{currentUser.name}', 没有相关的 pr",
                }
            )
    else:
        # 循环 prList, 添加到 resultDict 中
        for pr in targetMergeRequestAboutAlfredList:
            projectId = pr.projectId
            projectName = ""
            for cacheProject in projectCacheList:
                if cacheProject.id == projectId:
                    projectName = cacheProject.name
                    break
            
            # join to String
            reviewerNameListStr = ", ".join(pr.reviewerNameList)
            
            resultDict["items"].append(
                {
                    "title": pr.title,
                    "subtitle": f"project: {
                        projectName
                    }, requested by: {
                        pr.authorUserName
                    }, assignee: {
                        pr.assigneeName
                    }, reviewers: {
                        reviewerNameListStr
                    }",''
                    "arg": pr.webUrl,
                }
            )
        resultJsonForAlfred = json.dumps(resultDict)

    resultJsonForAlfred = json.dumps(resultDict)
    print(resultJsonForAlfred)
    
