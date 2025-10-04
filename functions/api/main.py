import json
from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app

from database.user_article_operations import (
    get_or_create_user, 
    get_unseen_articles, 
    get_articles_by_category, 
    search_articles, 
    get_bundled_articles_by_category
)
from config.config import config

# Import notification functions
from notifications.notification_functions import (
    update_fcm_token,
    set_notification_preference
)


set_global_options(
    max_instances=config.MAX_INSTANCES,
    region="asia-south1"
)

initialize_app()

@https_fn.on_call(region="asia-south1")
def get_unseen_articles_endpoint(req: https_fn.CallableRequest) -> https_fn.Response:
    """
    Get articles that user hasn't seen yet
    """
    try:
        auth_id = req.auth.uid
        
        # Get or create user
        user = get_or_create_user(auth_id)
        if not user:
            return {"error": "Failed to get or create user", "success": False}
            
        # Get query parameters
        limit = int(req.data['limit']['value']) if 'limit' in req.data else 10
        category = req.data['category'] if 'category' in req.data else None
        
        # Get unseen articles (always from the top, no offset needed)
        articles = get_unseen_articles(user.auth_id, limit, category)
        
        response_data = {
            "articles": articles,
            "limit": limit,
            "success": True
        }
        
        return response_data
        
    except Exception as e:
        error_message = f"Error fetching unseen articles: {str(e)}"
        print(error_message)
        return {"error": error_message, "success": False}




@https_fn.on_call(region="asia-south1")
def get_articles_by_category_endpoint(req: https_fn.CallableRequest) -> https_fn.Response:
    """
    Get articles by category with pagination
    """
    try:        
        # Get query parameters
        category = req.data['category'] if 'category' in req.data else None
        print(f"category: {category}")
        limit = int(req.data['limit']['value']) if 'limit' in req.data else 10
        offset = int(req.data['offset']['value']) if 'offset' in req.data else 0
        
        if not category:
            return {"error": "category parameter is required", "success": False}
        
        # Get articles by category
        articles = get_articles_by_category(category, limit, offset)
        
        response_data = {
            "articles": articles,
            "category": category,
            "limit": limit,
            "offset": offset,
            "success": True
        }
        
        return response_data
        
    except Exception as e:
        error_message = f"Error fetching articles by category: {str(e)}"
        print(error_message)
        return {"error": error_message, "success": False}


@https_fn.on_call(region="asia-south1")
def search_articles_endpoint(req: https_fn.CallableRequest) -> https_fn.Response:
    """
    Search articles by title and content with pagination
    """
    try:
        auth_id = req.auth.uid
        
        # Get or create user
        user = get_or_create_user(auth_id)
        if not user:
            return https_fn.Response(
                json.dumps({"error": "Failed to get or create user", "success": False}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
        
        # Get query parameters
        query = req.data['q'] if 'q' in req.data else None
        limit = int(req.data['limit']['value']) if 'limit' in req.data else 10
        offset = int(req.data['offset']['value']) if 'offset' in req.data else 0
        category = req.data['category'] if 'category' in req.data else None
        
        if not query:
            return https_fn.Response(
                json.dumps({"error": "query parameter 'q' is required", "success": False}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Search articles
        articles = search_articles(query, limit, offset, category)
        
        response_data = {
            "articles": articles,
            "query": query,
            "category": category,
            "limit": limit,
            "offset": offset,
            "success": True
        }
        
        return response_data
        
    except Exception as e:
        error_message = f"Error searching articles: {str(e)}"
        print(error_message)
        return {"error": error_message, "success": False}


@https_fn.on_call(region="asia-south1")
def get_bundled_articles_endpoint(req: https_fn.CallableRequest) -> https_fn.Response:
    """
    Get articles from each category bundled together
    """
    try:
        # Get query parameters
        limit_per_category = int(req.data['limit_per_category']['value']) if 'limit_per_category' in req.data else 5
        print(f"limit_per_category: {limit_per_category}")
        # Get bundled articles from all categories
        bundled_data = get_bundled_articles_by_category(limit_per_category)
        
        if not bundled_data["success"]:
            return https_fn.Response(
                json.dumps(bundled_data),
                status=500, 
                headers={"Content-Type": "application/json"}
            )
        
        response_data = {
            "categories": bundled_data["categories"],
            "total_categories": bundled_data["total_categories"],
            "limit_per_category": limit_per_category,
            "success": True
        }
        
        return response_data
        
    except Exception as e:
        error_message = f"Error fetching bundled articles: {str(e)}"
        print(error_message)
        return https_fn.Response(
            json.dumps({"error": error_message, "success": False}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


# Notification Functions
@https_fn.on_call(region="asia-south1")
def update_fcm_token_endpoint(req: https_fn.CallableRequest) -> https_fn.Response:
    """Update FCM token for a user"""
    result = update_fcm_token(req)
    return result

@https_fn.on_call(region="asia-south1")
def set_notification_preference_endpoint(req: https_fn.CallableRequest) -> https_fn.Response:
    """Set notification preference for a user (enable/disable)"""
    result = set_notification_preference(req)
    return result


