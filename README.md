# About the project
To access the source website, this Flask Application with Selenium and celery built on top of Docker uses the Google Chrome browser. After that, it can download the files by logging into the website with the provided credentials. Sometimes there is google captcha, so it bypass that as well.

When client hit the api end with valid parameters.
It left the task running asynchronously and response with 202 (Request Accepted) header code. Which states that their request is accepted and in processing.

This application was going to be use by other flask developer. I have to focus on main functionality to get POC and deliver it. So, I didn't bother efforts writing test suits and sanitizing the user incoming request in flask view. I'm also not logging the data just printing because in docker logs we can see it and the developer who is going to use this project, would probably

## Architecture
since its just backend system. you can see the project architecture and directory structure setup.

src - directory contains application source code.
static - this would contain the downloaded and static files.


The main logic is contained in the bot package in form of code.
