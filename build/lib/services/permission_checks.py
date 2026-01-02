from fastapi import Depends, HTTPException, status, Request


def required_roles(*allowed_roles: str):
    def dependency(request: Request):
        user = request.state.user
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized")
        return user
    return dependency


def permission_required(*permission: str):
    def dependency(request: Request):
        user = request.state.user
        if user.permission not in permission:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized"
            )
        return user
    return dependency

