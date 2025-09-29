"""
Test endpoints without authentication for development and testing
These endpoints should NOT be deployed to production
"""

import json
from firebase_functions import https_fn

from database.user_article_operations import (
    get_unseen_articles, 
    get_articles_by_category, 
    search_articles, 
    get_bundled_articles_by_category
)
from scraping.news_scraper import scrape_and_process_articles


@https_fn.on_request(region="asia-south1")
def test_get_unseen_articles_endpoint(req: https_fn.Request) -> https_fn.Response:
    """
    TEST ENDPOINT: Get articles that user hasn't seen yet (NO AUTH REQUIRED)
    WARNING: This endpoint bypasses authentication - use only for testing
    """
    try:
        # Get query parameters
        limit = int(req.args.get('limit', 10))
        category = req.args.get('category')
        
        # Use a test user ID for testing
        test_user_id = "test-user-123"
        
        # Get unseen articles
        articles = get_unseen_articles(test_user_id, limit, category)
        
        response_data = {
            "articles": articles,
            "limit": limit,
            "category": category,
            "test_mode": True,
            "test_user_id": test_user_id,
            "success": True
        }
        
        return https_fn.Response(
            json.dumps(response_data, default=str),
            status=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        error_message = f"Error fetching unseen articles: {str(e)}"
        print(error_message)
        return https_fn.Response(
            json.dumps({"error": error_message, "success": False, "test_mode": True}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@https_fn.on_request(region="asia-south1")
def test_get_articles_by_category_endpoint(req: https_fn.Request) -> https_fn.Response:
    """
    TEST ENDPOINT: Get articles by category with pagination (NO AUTH REQUIRED)
    WARNING: This endpoint bypasses authentication - use only for testing
    """
    try:
        # Get query parameters
        category = req.args.get('category')
        limit = int(req.args.get('limit', 10))
        offset = int(req.args.get('offset', 0))
        
        if not category:
            return https_fn.Response(
                json.dumps({"error": "category parameter is required", "success": False, "test_mode": True}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Get articles by category
        articles = get_articles_by_category(category, limit, offset)
        
        response_data = {
            "articles": articles,
            "category": category,
            "limit": limit,
            "offset": offset,
            "test_mode": True,
            "success": True
        }
        
        return https_fn.Response(
            json.dumps(response_data, default=str),
            status=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        error_message = f"Error fetching articles by category: {str(e)}"
        print(error_message)
        return https_fn.Response(
            json.dumps({"error": error_message, "success": False, "test_mode": True}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@https_fn.on_request(region="asia-south1")
def test_search_articles_endpoint(req: https_fn.Request) -> https_fn.Response:
    """
    TEST ENDPOINT: Search articles by title and content with pagination (NO AUTH REQUIRED)
    WARNING: This endpoint bypasses authentication - use only for testing
    """
    try:
        # Get query parameters
        query = req.args.get('q')
        limit = int(req.args.get('limit', 10))
        offset = int(req.args.get('offset', 0))
        category = req.args.get('category')
        
        if not query:
            return https_fn.Response(
                json.dumps({"error": "query parameter 'q' is required", "success": False, "test_mode": True}),
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
            "test_mode": True,
            "success": True
        }
        
        return https_fn.Response(
            json.dumps(response_data, default=str),
            status=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        error_message = f"Error searching articles: {str(e)}"
        print(error_message)
        return https_fn.Response(
            json.dumps({"error": error_message, "success": False, "test_mode": True}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@https_fn.on_request(region="asia-south1")
def test_get_bundled_articles_endpoint(req: https_fn.Request) -> https_fn.Response:
    """
    TEST ENDPOINT: Get articles from each category bundled together (NO AUTH REQUIRED)
    WARNING: This endpoint bypasses authentication - use only for testing
    OPTIMIZED: Now uses single database query for better performance
    """
    import time
    
    try:
        # Get query parameters
        limit_per_category = int(req.args.get('limit_per_category', 5))
        
        # Performance monitoring
        start_time = time.time()
        print(f"Starting bundled articles fetch with limit_per_category={limit_per_category}")
        
        # Get bundled articles from all categories
        bundled_data = get_bundled_articles_by_category(limit_per_category)
        
        # Calculate performance metrics
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Bundled articles fetch completed in {execution_time:.2f} seconds")
        
        if not bundled_data["success"]:
            return https_fn.Response(
                json.dumps({**bundled_data, "test_mode": True}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
        
        response_data = {
            "categories": bundled_data["categories"],
            "total_categories": bundled_data["total_categories"],
            "limit_per_category": limit_per_category,
            "performance": {
                "execution_time_seconds": round(execution_time, 2),
                "optimized_query": True
            },
            "test_mode": True,
            "success": True
        }
        
        return https_fn.Response(
            json.dumps(response_data, default=str),
            status=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        error_message = f"Error fetching bundled articles: {str(e)}"
        print(error_message)
        return https_fn.Response(
            json.dumps({"error": error_message, "success": False, "test_mode": True}),
            status=500,
            headers={"Content-Type": "application/json"}
        )


@https_fn.on_request(region="asia-south1")
def test_manual_scraping_endpoint(req: https_fn.Request) -> https_fn.Response:
    """
    Manually trigger news scraping (NO AUTH REQUIRED).
    This endpoint allows you to manually trigger the scraping process for testing.
    """
    try:
        print("Starting manual news scraping...")
        
        # Call the scraping function
        saved_count = scrape_and_process_articles()
        
        response_data = {
            "message": "Manual scraping completed successfully",
            "articles_saved": saved_count,
            "test_mode": True,
            "success": True
        }
        
        return https_fn.Response(
            json.dumps(response_data, default=str),
            status=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        error_message = f"Error in manual scraping: {str(e)}"
        print(error_message)
        return https_fn.Response(
            json.dumps({"error": error_message, "test_mode": True, "success": False}),
            status=500,
            headers={"Content-Type": "application/json"}
        )
