"""
This file is used as routes for the article app API's.
"""

from django.conf.urls import url
from .views import (
    AddArticleAPIView,
    LikeArticleAPIView,
    SearchArticleAPIView,
    DeleteArticleAPIView,
    UpdateArticleAPIView,
    GetArticleListAPIView,
    DisLikeArticleAPIView,
    BannerCreateAPIView,
    ListBannersAPIView,
    BannerUpdateAPIView,
    BannerDeleteAPIView,
    TestimonialCreateAPIView,
    ListTestimonialsAPIView,
    ListApprovedTestimonialsAPIView,
    TestimonialUpdateAPIView,
    TestimonialDeleteAPIView,
    CelebrityCategoryCreateAPIView,
    ListCelebrityCategoriesAPIView,
    CelebrityCreateAPIView,
    ListCelebrityAPIView,
    CelebrityUpdateAPIView,
    CelebrityDeleteAPIView,
    PopularBlogList,
    GetArticleDetailAPI,
    UpdateArticleSlug,
    LikeDislikeArticleAPIView,
    GetArticleSlugsAPI,
    BlogCreateAPIView,
)


urlpatterns = [
    url("v1/articleSlugList", GetArticleSlugsAPI.as_view(), name="article-slug-list"),
    url(
        "v1/articleLikeDislike/(?P<pk>.+)",
        LikeDislikeArticleAPIView.as_view(),
        name="article-like-dislike",
    ),
    url("v1/addArticle", AddArticleAPIView.as_view(), name="add-article"),
    url("addArticle", AddArticleAPIView.as_view(), name="add-article"),
    url("v1/popularBlogs", PopularBlogList.as_view(), name="popular-blogs"),
    url(
        "v1/getArticleDetail/(?P<slug>.+)",
        GetArticleDetailAPI.as_view(),
        name="article-detail",
    ),
    url(
        "v1/updateArticleSlug", UpdateArticleSlug.as_view(), name="update-article-slug"
    ),
    url("v1/getArticleList", GetArticleListAPIView.as_view(), name="get-articles"),
    url("getArticleList", GetArticleListAPIView.as_view(), name="get-articles"),
    url("v1/searchArticle", SearchArticleAPIView.as_view(), name="search-article"),
    url("searchArticle", SearchArticleAPIView.as_view(), name="search-article"),
    url("v1/likeArticle/(?P<pk>.+)", LikeArticleAPIView.as_view(), name="like-article"),
    url("likeArticle/(?P<pk>.+)", LikeArticleAPIView.as_view(), name="like-article"),
    url(
        "v1/updateArticle/(?P<pk>.+)",
        UpdateArticleAPIView.as_view(),
        name="update-article",
    ),
    url(
        "updateArticle/(?P<pk>.+)",
        UpdateArticleAPIView.as_view(),
        name="update-article",
    ),
    url(
        "v1/deleteArticle/(?P<pk>.+)",
        DeleteArticleAPIView.as_view(),
        name="delete-article",
    ),
    url(
        "deleteArticle/(?P<pk>.+)",
        DeleteArticleAPIView.as_view(),
        name="delete-article",
    ),
    url("v1/likeArticle/(?P<pk>.+)", LikeArticleAPIView.as_view(), name="like-article"),
    url("likeArticle/(?P<pk>.+)", LikeArticleAPIView.as_view(), name="like-article"),
    url("v1/dislikeArticle", DisLikeArticleAPIView.as_view(), name="unlike-article"),
    url("dislikeArticle", DisLikeArticleAPIView.as_view(), name="unlike-article"),
    # Banners
    url("v1/createBanner", BannerCreateAPIView.as_view(), name="create-banner"),
    url("v1/listBanners", ListBannersAPIView.as_view(), name="list-banners"),
    url(
        "v1/updateBanner/(?P<pk>.+)",
        BannerUpdateAPIView.as_view(),
        name="update-banner",
    ),
    url(
        "v1/deleteBanner/(?P<pk>.+)",
        BannerDeleteAPIView.as_view(),
        name="delete-banner",
    ),
    # Testimonial
    url(
        "v1/createTestimonial",
        TestimonialCreateAPIView.as_view(),
        name="create-testimonial",
    ),
    url(
        "v1/listTestimonials",
        ListTestimonialsAPIView.as_view(),
        name="list-testimonials",
    ),
    url(
        "v1/listApprovedTestimonials",
        ListApprovedTestimonialsAPIView.as_view(),
        name="approved-testimonials",
    ),
    url(
        "v1/updateTestimonial/(?P<pk>.+)",
        TestimonialUpdateAPIView.as_view(),
        name="update-testimonial",
    ),
    url(
        "v1/deleteTestimonial/(?P<pk>.+)",
        TestimonialDeleteAPIView.as_view(),
        name="delete-testimonial",
    ),
    # Celebrity
    url(
        "v1/createCelebCategory",
        CelebrityCategoryCreateAPIView.as_view(),
        name="create-celeb-category",
    ),
    url(
        "v1/listCelebCategories",
        ListCelebrityCategoriesAPIView.as_view(),
        name="list-celeb-categories",
    ),
    url(
        "v1/createCelebrity", CelebrityCreateAPIView.as_view(), name="create-celebrity"
    ),
    url("v1/listCelebrity", ListCelebrityAPIView.as_view(), name="list-celebrity"),
    url(
        "v1/updateCelebrity/(?P<pk>.+)",
        CelebrityUpdateAPIView.as_view(),
        name="update-Celebrity",
    ),
    url(
        "v1/deleteCelebrity/(?P<pk>.+)",
        CelebrityDeleteAPIView.as_view(),
        name="delete-Celebrity",
    ),
    # Blogs
    url("createBlog", BlogCreateAPIView.as_view(), name="create-blog"),
]

