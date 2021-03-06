# Fairwinds_Interview_Challenge
Fairwinds Interview Challenge

# Assignment

* Using any language you prefer, write code that brings up an EC2 instance running the default page of a web application after running a single command.
* The command can (and likely will) call a longer shell script, or other configuration management code.
* The web application can be any common framework (Django, Rails, Symfony, etc.), but not the default Nginx or Apache setup.
* Your credentials are attached (including the assigned region). The credentials do not have access to EKS, ECS, S3, ELB, ASG`:WQ, or Route53.
* If needed, you can manually create pre-requisites such as ssh key pairs and the like. 
* _Before the script is run, there should be no compute instances running and afterward the script should output the address of your working web application._

# Evaluation Criteria 

* Please don't take more than 3 hours total over the next few days. 
* Timekeeping is up to you and we expect your finished response in a reasonable amount of time.
* You are being evaluated based on the quality of your code and configuration, on the clarity of your communication, and on project presentation.
* Source control is expected as well as documentation that should explain how you approached the challenge, what assumptions you've made, and reasoning behind the choices in your approach.


Please reach out with any questions or clarifications.
Good Luck!

## Executing the Script
Retrieve pem key from AWS

Git clone script to local machine

Set the appropriate environment variables (AWS_SECRET_KEY,AWS_ACCESS_KEY,PEM_KEY)

Run:
  *python3 ec2_generator.py*

## Expected Outcome

The script should facilitate the creation of an EC2 instance with the appropriate security group and 

## Methodology
I decided to install a symfony web application.

First, locate the AMI, there was not one preloaded for me, so I used the standard AWS RedHat one

There was no VPC; I created one with all default settings

No Security Group, so I created one, allowing ingress for port 22 on my public IP and port 8000 for symfony

Create key pair

In my mind, I logically separated the script into 3 parts, build the instance, access the instance, build symfony

### Build the Instance

This was fairly straightforward. I used the boto3 module in python. Key values and the location of the PEM file are environment variables that need to be set prior to successful execution of the script. Without spending too much extra time, I set out to make the script as resilient as possible. The script successfully waits for the the VM to build and then checks that it can access the server prior to moving on to the next step.

### Access the Instance

This is actually the part that gave me the most trouble. I originally started working with the paramiko module in python, but I had trouble accessing the server with the pem key. After enough head banging, I switched over to the fabric module and it worked right away.

### Build Symfony

I wrote the install script for symfony as a string inside the python script. This seemed easier after I established the minimal amount of steps necessary to accomplish the task. This also allowed me to push the entire script and run it all with one command.

