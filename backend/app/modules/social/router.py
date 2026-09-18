from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from backend.app.models.engine import get_session
from backend.app.modules.social.schema import (
    PostCreateRequest, PostResponse, CommentCreateRequest, CommentResponse, 
    TranslateRequest, NotificationResponse, ThreadCreateRequest, ThreadResponse,
    MarketItemCreateRequest, MarketItemResponse, HazardReportCreateRequest, HazardReportResponse,
    MeetupCreateRequest, MeetupResponse, ThreadCommentCreateRequest, ThreadCommentResponse,
    MarketCommentCreateRequest, MarketCommentResponse, MeetupCommentCreateRequest, MeetupCommentResponse,
    HazardCommentCreateRequest, HazardCommentResponse
)
from backend.app.models.database import Post, User, Comment, Like, Notification, Thread, ThreadComment, MarketItem, HazardReport, Meetup, MeetupAttendee, MarketComment, MeetupComment, HazardComment
from backend.app.modules.social.tasks import fetch_weather_for_post
from backend.app.modules.surf.agents import surf_report_subagent
from sqlalchemy import func
import re
from datetime import datetime
import httpx

def dispatch_notification(db: Session, receiver_id: int, sender_id: int, entity_id: int, entity_type: str, action_type: str):
    if receiver_id == sender_id: return
    sender = db.get(User, sender_id)
    if not sender: return
    sender_name = sender.username
    
    existing_notif = db.exec(select(Notification).where(
        Notification.user_id == receiver_id,
        Notification.entity_id == entity_id,
        Notification.entity_type == entity_type,
        Notification.type == action_type,
        Notification.is_read == False
    )).first()

    if existing_notif:
        count = 1
        if action_type == "like":
            count = db.exec(select(func.count()).where(Like.post_id == entity_id)).first()
        elif action_type == "comment" and entity_type == "post":
            count = db.exec(select(func.count()).where(Comment.post_id == entity_id)).first()
        elif action_type == "comment" and entity_type == "thread":
            count = db.exec(select(func.count()).where(ThreadComment.thread_id == entity_id)).first()
        elif action_type == "comment" and entity_type == "market":
            count = db.exec(select(func.count()).where(MarketComment.item_id == entity_id)).first()
        elif action_type == "comment" and entity_type == "meetup":
            count = db.exec(select(func.count()).where(MeetupComment.meetup_id == entity_id)).first()
        elif action_type == "comment" and entity_type == "hazard":
            count = db.exec(select(func.count()).where(HazardComment.report_id == entity_id)).first()
        elif action_type == "attend":
            count = db.exec(select(func.count()).where(MeetupAttendee.meetup_id == entity_id)).first()

        others_count = max(0, count - 1)
        
        if others_count > 0:
            if action_type == "like":
                existing_notif.message = f"{sender_name} and {others_count} others liked your {entity_type}."
            elif action_type == "comment":
                existing_notif.message = f"{sender_name} and {others_count} others commented on your {entity_type}."
            elif action_type == "attend":
                existing_notif.message = f"{sender_name} and {others_count} others joined your meetup."
        else:
            if action_type == "like":
                existing_notif.message = f"{sender_name} liked your {entity_type}."
            elif action_type == "comment":
                existing_notif.message = f"{sender_name} commented on your {entity_type}."
            elif action_type == "attend":
                existing_notif.message = f"{sender_name} joined your meetup."

        existing_notif.sender_id = sender_id
        existing_notif.created_at = datetime.utcnow()
        db.add(existing_notif)
    else:
        if action_type in ["like", "comment"]:
            other_type = "comment" if action_type == "like" else "like"
            same_user_other_notif = db.exec(select(Notification).where(
                Notification.user_id == receiver_id,
                Notification.sender_id == sender_id,
                Notification.entity_id == entity_id,
                Notification.entity_type == entity_type,
                Notification.type == other_type,
                Notification.is_read == False
            )).first()
            if same_user_other_notif:
                same_user_other_notif.type = "like_comment"
                same_user_other_notif.message = f"{sender_name} liked and commented on your {entity_type}."
                same_user_other_notif.created_at = datetime.utcnow()
                db.add(same_user_other_notif)
                db.commit()
                return

        msg = ""
        if action_type == "like": msg = f"{sender_name} liked your {entity_type}."
        elif action_type == "comment": msg = f"{sender_name} commented on your {entity_type}."
        elif action_type == "attend": msg = f"{sender_name} joined your meetup."
        else: msg = f"{sender_name} interacted with your {entity_type}."

        notif = Notification(
            user_id=receiver_id,
            sender_id=sender_id,
            entity_id=entity_id,
            entity_type=entity_type,
            type=action_type,
            message=msg
        )
        db.add(notif)
    db.commit()

def notify_mentioned_users(db: Session, text: str, sender_id: int, entity_id: int, entity_type: str):
    if not text: return
    mentions = set(re.findall(r"@(\w+)", text))
    sender = db.get(User, sender_id)
    sender_name = sender.username if sender else "Someone"
    
    for username in mentions:
        mentioned_user = db.exec(select(User).where(User.username == username)).first()
        if mentioned_user and mentioned_user.id != sender_id:
            existing_notif = db.exec(select(Notification).where(
                Notification.user_id == mentioned_user.id,
                Notification.entity_id == entity_id,
                Notification.entity_type == entity_type,
                Notification.type == "mention",
                Notification.is_read == False
            )).first()

            if existing_notif and existing_notif.sender_id != sender_id:
                existing_notif.message = f"{sender_name} and others mentioned you in a {entity_type}."
                existing_notif.sender_id = sender_id
                existing_notif.created_at = datetime.utcnow()
                db.add(existing_notif)
            elif not existing_notif:
                notif = Notification(
                    user_id=mentioned_user.id,
                    sender_id=sender_id,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    type="mention",
                    message=f"{sender_name} mentioned you in a {entity_type}."
                )
                db.add(notif)
    db.commit()

router = APIRouter()

@router.post("/posts", response_model=PostResponse)
async def create_post(request: PostCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_post = Post(
        user_id=request.user_id,
        location=request.location,
        category=request.category,
        caption=request.caption,
        media_url=request.media_url,
        media_urls=request.media_urls
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    if new_post.category in ["Session", "Alert"]:
        fetch_weather_for_post.delay(new_post.id)
    else:
        # Prevent UI from showing pending sync for irrelevant categories
        new_post.ai_weather_synced = True
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        
    response_data = {**new_post.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url, "comments": []}
    
    notify_mentioned_users(db, new_post.caption, new_post.user_id, new_post.id, "post")
    
    return response_data

@router.get("/posts", response_model=List[PostResponse])
async def get_all_posts(limit: int = 20, offset: int = 0, db: Session = Depends(get_session)):
    statement = select(Post).order_by(Post.created_at.desc()).offset(offset).limit(limit)
    posts = db.exec(statement).all()
    
    result = []
    for p in posts:
        post_data = {**p.dict(), "username": p.user.username, "profile_pic_url": p.user.profile_pic_url, "comments": [], "likes_count": len(p.likes), "liked_by_users": [like.user_id for like in p.likes]}
        for c in p.comments:
            post_data["comments"].append({
                **c.dict(),
                "username": c.user.username,
                "profile_pic_url": c.user.profile_pic_url
            })
        result.append(post_data)
        
    return result

@router.post("/posts/{post_id}/comments", response_model=dict)
async def create_comment(post_id: int, request: CommentCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    post = db.get(Post, post_id)
    
    if not user or not post:
        raise HTTPException(status_code=404, detail="User or Post not found.")
        
    new_comment = Comment(
        post_id=post_id,
        user_id=request.user_id,
        content=request.content
    )
    db.add(new_comment)
    
    post_owner = db.get(User, post.user_id)
    mentions = set(re.findall(r"@(\w+)", request.content))
    post_owner_mentioned = post_owner and post_owner.username in mentions
    
    if post.user_id != request.user_id and not post_owner_mentioned:
        dispatch_notification(db, post.user_id, request.user_id, post.id, "post", "comment")
        
    db.commit()
    db.refresh(new_comment)
    
    response_data = {"id": new_comment.id, "content": new_comment.content, "username": user.username, "profile_pic_url": user.profile_pic_url}
    
    notify_mentioned_users(db, new_comment.content, new_comment.user_id, post.id, "post")
    
    return response_data

@router.post("/posts/{post_id}/like")
async def toggle_like(post_id: int, user_id: int, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    post = db.get(Post, post_id)
    if not user or not post:
        raise HTTPException(status_code=404, detail="User or Post not found.")
        
    existing_like = db.exec(select(Like).where(Like.post_id == post_id, Like.user_id == user_id)).first()
    if existing_like:
        db.delete(existing_like)
        
        if post.user_id != user_id:
            # Downgrade or remove notification
            notif = db.exec(select(Notification).where(
                Notification.user_id == post.user_id,
                Notification.sender_id == user_id,
                Notification.entity_id == post.id,
                Notification.entity_type == "post",
                Notification.type.in_(["like", "like_comment"])
            )).first()
            if notif:
                if notif.type == "like_comment":
                    notif.type = "comment"
                    notif.message = f"{user.username} commented on your {post.category} post."
                else:
                    db.delete(notif)
                    
        db.commit()
        return {"status": "unliked"}
    else:
        new_like = Like(post_id=post_id, user_id=user_id)
        db.add(new_like)
        if post.user_id != user_id:
            dispatch_notification(db, post.user_id, user_id, post.id, "post", "like")
        db.commit()
        return {"status": "liked"}

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(user_id: int, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    statement = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(30)
    notifs = db.exec(statement).all()
    
    res = []
    for n in notifs:
        sender = db.get(User, n.sender_id)
        res.append({**n.dict(), "sender_name": sender.username if sender else "Someone"})
    return res

@router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int, db: Session = Depends(get_session)):
    notif = db.get(Notification, notif_id)
    if notif:
        notif.is_read = True
        db.add(notif)
        db.commit()
    return {"status": "success"}

@router.put("/notifications/read-all")
async def mark_all_notifications_read(user_id: int, db: Session = Depends(get_session)):
    notifs = db.exec(select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)).all()
    for notif in notifs:
        notif.is_read = True
        db.add(notif)
    db.commit()
    return {"status": "success"}

@router.post("/translate")
async def translate_text(request: TranslateRequest):
    prompt = (
        f"Translate the following surf-related text to Indonesian. Keep the tone casual and cool for surfers.\n\n"
        f"Text: '{request.text}'\n\n"
        f"Return ONLY the translated text, nothing else."
    )
    try:
        res = surf_report_subagent.run(prompt)
        content = res.content if hasattr(res, 'content') else str(res)
        return {"translated_text": content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/search")
async def search_users(q: str = "", limit: int = 5, db: Session = Depends(get_session)):
    if len(q) < 1:
        return []
    statement = select(User).where(User.username.ilike(f"%{q}%")).limit(limit)
    users = db.exec(statement).all()
    return [{"id": u.id, "username": u.username, "profile_pic_url": u.profile_pic_url} for u in users]

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, user_id: int, db: Session = Depends(get_session)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this post")
        
    # Delete associated comments and likes
    for comment in post.comments:
        db.delete(comment)
    for like in post.likes:
        db.delete(like)
        
    # Delete associated notifications
    notifs = db.exec(select(Notification).where(Notification.entity_id == post_id, Notification.entity_type == 'post')).all()
    for notif in notifs:
        db.delete(notif)
        
    db.delete(post)
    db.commit()
    
    return {"message": "Post deleted successfully"}

@router.delete("/posts/comments/{comment_id}")
async def delete_post_comment(comment_id: int, user_id: int, db: Session = Depends(get_session)):
    comment = db.get(Comment, comment_id)
    if not comment: raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return {"status": "success"}


# ==========================================
# V3: COMMUNITY ROUTES (THREADS & MARKET)
# ==========================================

@router.post("/threads", response_model=ThreadResponse)
async def create_thread(request: ThreadCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_thread = Thread(**request.dict())
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    
    return {**new_thread.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url}

@router.get("/threads", response_model=List[ThreadResponse])
async def get_threads(limit: int = 50, offset: int = 0, db: Session = Depends(get_session)):
    statement = select(Thread).order_by(Thread.created_at.desc()).offset(offset).limit(limit)
    threads = db.exec(statement).all()
    
    results = []
    for t in threads:
        t_dict = {**t.dict(), "username": t.user.username, "profile_pic_url": t.user.profile_pic_url}
        t_dict["comments"] = [{**c.dict(), "username": c.user.username, "profile_pic_url": c.user.profile_pic_url} for c in t.comments]
        results.append(t_dict)
    return results

@router.post("/threads/{thread_id}/comments", response_model=ThreadCommentResponse)
async def create_thread_comment(thread_id: int, request: ThreadCommentCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    new_comment = ThreadComment(thread_id=thread_id, user_id=user.id, content=request.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    notify_mentioned_users(db, new_comment.content, new_comment.user_id, thread.id, "thread")
    dispatch_notification(db, thread.user_id, new_comment.user_id, thread.id, "thread", "comment")
    
    return {**new_comment.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url}

@router.post("/market", response_model=MarketItemResponse)
async def create_market_item(request: MarketItemCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_item = MarketItem(**request.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {**new_item.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url}

@router.get("/market", response_model=List[MarketItemResponse])
async def get_market_items(limit: int = 50, offset: int = 0, db: Session = Depends(get_session)):
    statement = select(MarketItem).order_by(MarketItem.created_at.desc()).offset(offset).limit(limit)
    items = db.exec(statement).all()
    
    results = []
    for i in items:
        i_dict = {**i.dict(), "username": i.user.username, "profile_pic_url": i.user.profile_pic_url}
        i_dict["comments"] = [{**c.dict(), "username": c.user.username, "profile_pic_url": c.user.profile_pic_url} for c in i.comments]
        results.append(i_dict)
    return results

@router.post("/market/{item_id}/sold")
async def mark_market_item_sold(item_id: int, user_id: int, db: Session = Depends(get_session)):
    item = db.get(MarketItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    item.status = "Sold"
    db.add(item)
    db.commit()
    return {"status": "success"}

@router.post("/market/{item_id}/comments", response_model=MarketCommentResponse)
async def create_market_comment(item_id: int, request: MarketCommentCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    item = db.get(MarketItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    new_comment = MarketComment(market_item_id=item_id, user_id=user.id, content=request.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    notify_mentioned_users(db, new_comment.content, new_comment.user_id, item.id, "market")
    dispatch_notification(db, item.user_id, new_comment.user_id, item.id, "market", "comment")
    
    return {**new_comment.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url}

@router.post("/meetups", response_model=MeetupResponse)
async def create_meetup(request: MeetupCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_meetup = Meetup(**request.dict())
    db.add(new_meetup)
    db.commit()
    db.refresh(new_meetup)
    
    return {**new_meetup.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url}

@router.get("/meetups", response_model=List[MeetupResponse])
async def get_meetups(limit: int = 50, offset: int = 0, db: Session = Depends(get_session)):
    statement = select(Meetup).order_by(Meetup.created_at.desc()).offset(offset).limit(limit)
    meetups = db.exec(statement).all()
    
    results = []
    for m in meetups:
        m_dict = {**m.dict(), "username": m.user.username, "profile_pic_url": m.user.profile_pic_url}
        m_dict["attendees"] = [a.user.username for a in m.attendees]
        m_dict["comments"] = [{**c.dict(), "username": c.user.username, "profile_pic_url": c.user.profile_pic_url} for c in m.comments]
        results.append(m_dict)
        
    return results

@router.post("/meetups/{meetup_id}/comments", response_model=MeetupCommentResponse)
async def create_meetup_comment(meetup_id: int, request: MeetupCommentCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    meetup = db.get(Meetup, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
        
    new_comment = MeetupComment(meetup_id=meetup_id, user_id=user.id, content=request.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    notify_mentioned_users(db, new_comment.content, new_comment.user_id, meetup.id, "meetup")
    dispatch_notification(db, meetup.user_id, new_comment.user_id, meetup.id, "meetup", "comment")
    
    return {**new_comment.dict(), "username": user.username, "profile_pic_url": user.profile_pic_url}

@router.post("/meetups/{meetup_id}/join")
async def join_meetup(meetup_id: int, user_id: int, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    meetup = db.get(Meetup, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
        
    # Check if already joined
    existing = db.exec(select(MeetupAttendee).where(MeetupAttendee.meetup_id == meetup_id).where(MeetupAttendee.user_id == user_id)).first()
    if existing:
        return {"status": "already joined"}
        
    attendee = MeetupAttendee(meetup_id=meetup_id, user_id=user_id)
    db.add(attendee)
    db.commit()
    dispatch_notification(db, meetup.user_id, user_id, meetup.id, "meetup", "attend")
    return {"status": "success"}

# ==========================================
# V3: COMMUNITY DELETE ROUTES
# ==========================================

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: int, user_id: int, db: Session = Depends(get_session)):
    thread = db.get(Thread, thread_id)
    if not thread: raise HTTPException(status_code=404, detail="Thread not found")
    if thread.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    
    for comment in thread.comments:
        db.delete(comment)
    db.delete(thread)
    db.commit()
    return {"status": "success"}

@router.delete("/threads/comments/{comment_id}")
async def delete_thread_comment(comment_id: int, user_id: int, db: Session = Depends(get_session)):
    comment = db.get(ThreadComment, comment_id)
    if not comment: raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return {"status": "success"}

@router.delete("/market/{item_id}")
async def delete_market_item(item_id: int, user_id: int, db: Session = Depends(get_session)):
    item = db.get(MarketItem, item_id)
    if not item: raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    
    for comment in item.comments:
        db.delete(comment)
    db.delete(item)
    db.commit()
    return {"status": "success"}

@router.delete("/market/comments/{comment_id}")
async def delete_market_comment(comment_id: int, user_id: int, db: Session = Depends(get_session)):
    comment = db.get(MarketComment, comment_id)
    if not comment: raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return {"status": "success"}

@router.delete("/meetups/{meetup_id}")
async def delete_meetup(meetup_id: int, user_id: int, db: Session = Depends(get_session)):
    meetup = db.get(Meetup, meetup_id)
    if not meetup: raise HTTPException(status_code=404, detail="Meetup not found")
    if meetup.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    
    for attendee in meetup.attendees:
        db.delete(attendee)
    for comment in meetup.comments:
        db.delete(comment)
    db.delete(meetup)
    db.commit()
    return {"status": "success"}

@router.delete("/meetups/comments/{comment_id}")
async def delete_meetup_comment(comment_id: int, user_id: int, db: Session = Depends(get_session)):
    comment = db.get(MeetupComment, comment_id)
    if not comment: raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return {"status": "success"}

# ==========================================
# V3: HAZARD ALERT ROUTES
# ==========================================

@router.post("/hazards", response_model=HazardReportResponse)
async def create_hazard_report(request: HazardReportCreateRequest, db: Session = Depends(get_session)):
    user = db.get(User, request.reporter_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Auto-geocode if client didn't provide coordinates
    lat = request.latitude
    lng = request.longitude
    if lat is None or lng is None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                geo_res = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": request.location, "format": "json", "limit": 1},
                    headers={"User-Agent": "OmbakNusantara/1.0"}
                )
                if geo_res.status_code == 200:
                    geo_data = geo_res.json()
                    if geo_data:
                        lat = float(geo_data[0]["lat"])
                        lng = float(geo_data[0]["lon"])
        except Exception:
            pass  # Geocoding optional — proceed without coords
        
    new_report = HazardReport(
        user_id=request.reporter_id,
        location=request.location,
        latitude=lat,
        longitude=lng,
        severity=request.severity,
        hazard_type=request.hazard_type,
        description=request.description,
        media_url=request.media_url
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return {**new_report.dict(), "reporter_id": new_report.user_id, "username": user.username, "profile_pic_url": user.profile_pic_url, "comments": []}

@router.get("/hazards", response_model=List[HazardReportResponse])
async def get_hazard_reports(limit: int = 50, offset: int = 0, db: Session = Depends(get_session)):
    statement = select(HazardReport).order_by(HazardReport.created_at.desc()).offset(offset).limit(limit)
    reports = db.exec(statement).all()
    
    result = []
    for r in reports:
        comments_data = []
        for c in r.comments:
            comments_data.append({**c.dict(), "username": c.user.username, "profile_pic_url": c.user.profile_pic_url})
        result.append({**r.dict(), "reporter_id": r.user_id, "username": r.user.username, "profile_pic_url": r.user.profile_pic_url, "comments": comments_data})
    
    return result

@router.post("/hazards/{report_id}/comments")
async def create_hazard_comment(report_id: int, request: HazardCommentCreateRequest, db: Session = Depends(get_session)):
    report = db.get(HazardReport, report_id)
    if not report: raise HTTPException(status_code=404, detail="Report not found")
    
    user = db.get(User, request.user_id)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    new_comment = HazardComment(report_id=report_id, user_id=request.user_id, content=request.content)
    db.add(new_comment)
    db.commit()
    notify_mentioned_users(db, new_comment.content, new_comment.user_id, report.id, "hazard")
    dispatch_notification(db, report.user_id, new_comment.user_id, report.id, "hazard", "comment")
    return {"status": "success"}

@router.delete("/hazards/{report_id}")
async def delete_hazard_report(report_id: int, user_id: int, db: Session = Depends(get_session)):
    report = db.get(HazardReport, report_id)
    if not report: raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(report)
    db.commit()
    return {"status": "success"}

@router.delete("/hazards/comments/{comment_id}")
async def delete_hazard_comment(comment_id: int, user_id: int, db: Session = Depends(get_session)):
    comment = db.get(HazardComment, comment_id)
    if not comment: raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id: raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return {"status": "success"}
