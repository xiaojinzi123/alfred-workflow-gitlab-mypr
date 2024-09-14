""" curl --request GET \
  --header "PRIVATE-TOKEN: glpat-3SAVZnAxw1ZPGeGkBX8k" \
  --url "https://gitlab.example.com/api/v4/groups/29/approval_rules" """

import os
import json
import dataclasses
import pathlib

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
    title: str
    webUrl: str
    authorUserName: str
    projectId: str
    assigneeId: str | None
    reviewerIdList: list[str]

if __name__ == '__main__':

    # 为了和 alfred 的输出分开
    isLog: bool = False

    gitlabToken = os.environ["gitlabToken"]
    if isLog:
        print(f"gitlabToken = {gitlabToken}")

    # 获取 PR 信息的 curl 命令
    targetPrUrl = f"curl --request GET --header 'PRIVATE-TOKEN: {gitlabToken}' --url 'https://gitlab.vistring.com/api/v4/merge_requests?scope=all&state=opened'"
    # 最后需要加上项目 Id
    targetProjectUrl = f"curl --request GET --header 'PRIVATE-TOKEN: {gitlabToken}' --url 'https://gitlab.vistring.com/api/v4/projects/'"
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
    prListJson = json.loads(
        os.popen(targetPrUrl).read()
    )
    for pr in prListJson:
        mergeRequestList.append(
            MergeRequest(
                title=pr.get("title"),
                webUrl=pr.get("web_url"),
                authorUserName=pr.get("author").get("username"),
                projectId=pr.get("project_id"),
                # assignee.id, assignee 对象可能为 None
                assigneeId=pr.get("assignee").get("id") if pr.get("assignee") else "None",
                reviewerIdList = [r.get("id") for r in pr.get("reviewers")]
            )
        )

    if isLog:
        print(f"mergeRequestList: {mergeRequestList}")

    # 从 mergeRequestList 中过滤出 assigneeId 或者 reviewerIdList 包含当前用户的 MergeRequest
    mergeRequestAboutYouList: list[MergeRequest] = []
    for pr in mergeRequestList:
        if currentUser.id == pr.assigneeId or currentUser.id in pr.reviewerIdList:
            mergeRequestAboutYouList.append(pr)

    # 从 projectCacheList 过滤出在 mergeRequestList 不存在的 projectId List
    cachedProjectIdList = [p.id for p in projectCacheList]
    # 拿到没有缓存的 Project 信息
    noCachedProjectIdList = []
    for pr in mergeRequestAboutYouList:
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

    targetMergeRequestAboutAlfredList = mergeRequestAboutYouList
    # targetMergeRequestAboutAlfredList = mergeRequestList

    if len(targetMergeRequestAboutAlfredList) == 0:
        resultDict["items"].append(
                {
                    "title": f"帅气逼人的 '{currentUser.name}', 没有您要待审批的 PR",
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

            resultDict["items"].append(
                {
                    "title": pr.title,
                    "subtitle": f"发起人: {pr.authorUserName}, 项目: {projectName}",
                    "arg": pr.webUrl,
                }
            )
        resultJsonForAlfred = json.dumps(resultDict)

    resultJsonForAlfred = json.dumps(resultDict)
    print(resultJsonForAlfred)
    
