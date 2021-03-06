class NOTIF:
    ActContent = 1
    ActCancel = 2
    RemovalFromAct = 3
    NewBoya = 4
    ActCommented = 5
    OrgApplyRes = 6
    BecomeOwner = 7
    BecomeAdmin = 8
    RemovalFromAdmin = 9
    ActCommentModified = 10
    GroundApplyReminder = 11


NOTIF_TYPE_CHOICES = {
    (NOTIF.ActContent, '参与的活动的内容变更通知'),
    (NOTIF.ActCancel, '参与的活动被取消通知'),
    (NOTIF.RemovalFromAct, '被移除出活动通知'),
    (NOTIF.NewBoya, '新博雅通知'),
    (NOTIF.ActCommented, '管理的活动被评价的通知'),
    (NOTIF.ActCommentModified, '管理的活动评论被修改的通知'),
    (NOTIF.OrgApplyRes, '创建组织请求审批结果'),
    (NOTIF.BecomeOwner, '被转让为负责人通知'),
    (NOTIF.BecomeAdmin, '被设置为管理员通知'),
    (NOTIF.RemovalFromAdmin, '被移出管理员通知'),
    (NOTIF.GroundApplyReminder, '场地预约提醒通知')
}

NOTIF_TYPE_DICT = {k[0]: k[1] for k in NOTIF_TYPE_CHOICES}


class BLOCKID:
    BOYA = 2
    PERSONAL = 5


class APPLY:
    MAX_TIME = 2
    MAX_DEFAULT = 3
    DISCOUNT = 0.9
