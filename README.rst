References:

FastAPI — How to add basic and cookie authentication
https://medium.com/data-rebels/fastapi-how-to-add-basic-and-cookie-authentication-a45c85ef47d3

https with url_for
https://github.com/encode/starlette/issues/538

Good JWT articles
https://hasura.io/blog/best-practices-of-using-jwt-with-graphql/
https://stormpath.com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage

There's so much that can go wrong when you're building one of these things.

* One wrong / can lead to a redirect that costs you your cookies. =[
* 'Authorization: Bearer' might not be exactly what your backend calls it.
