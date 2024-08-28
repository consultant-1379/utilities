
def getCoreServices(service):
    coreServices = []  #should include only those services providing the actual
                           #service(includes components) and exclude the aggregated services
    if service.getServices() == [] :
        coreServices.append(service)
    else :
        for serv in service.getServices() :
            coreServices.extend(getCoreServices(serv))

    return coreServices

def getCoreFunctions(function):
    coreFunctions = []  #should include only those services providing the actual
                           #service(includes components) and exclude the aggregated services
    if function.getFunctions() == [] :
        coreFunctions.append(function)
    else :
        for func in function.getFunctions() :
            coreFunctions.extend(getCoreFunctions(func))

    return coreFunctions
