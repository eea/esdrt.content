
def setupVarious(context):
    """ various import steps for esdrt.content """
    portal = context.getSite()

    if context.readDataFile('esdrt.content_various.txt') is None:
        return
