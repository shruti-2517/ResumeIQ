"""Tool declarations and execution handlers for the Autonomous Career Coach Agent."""

import logging
from typing import Any

from google.genai import types

logger = logging.getLogger(__name__)


def tool_search_learning_resources(skill_name: str) -> dict[str, Any]:
    """Search for top online courses, documentation, and open-source repositories for a given skill or missing knowledge area."""
    clean_skill = skill_name.strip() if isinstance(skill_name, str) else "Software Engineering"
    logger.info("Coach Agent searching learning resources for skill: %s", clean_skill)

    # Curated knowledge base of learning resources for technical & domain skills
    skill_lower = clean_skill.lower()

    courses = []
    github_repos = []

    if "python" in skill_lower or "fastapi" in skill_lower or "django" in skill_lower:
        courses = [
            {
                "title": "Complete Python Developer & Async Frameworks",
                "platform": "Coursera / Udemy",
                "url": "https://www.coursera.org/learn/python",
                "type": "Course",
                "description": "Master modern Python 3.12, asyncio, FastAPI, and production API design.",
            },
            {
                "title": "Official FastAPI Documentation & Tutorials",
                "platform": "Official Docs",
                "url": "https://fastapi.tiangolo.com/tutorial/",
                "type": "Documentation",
                "description": "Step-by-step interactive documentation for async web application development.",
            },
        ]
        github_repos = [
            {
                "name": "tiangolo/fastapi",
                "url": "https://github.com/tiangolo/fastapi",
                "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
            }
        ]
    elif "react" in skill_lower or "next" in skill_lower or "typescript" in skill_lower or "frontend" in skill_lower:
        courses = [
            {
                "title": "React & Next.js - The Complete Guide",
                "platform": "Udemy",
                "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/",
                "type": "Course",
                "description": "Build modern frontend applications with React 19, Next.js App Router, and TypeScript.",
            },
            {
                "title": "Full Stack Open - Deep Dive into Modern Web Development",
                "platform": "University of Helsinki",
                "url": "https://fullstackopen.com/en/",
                "type": "Interactive Course",
                "description": "Comprehensive open-source program covering React, Redux, Node.js, GraphQL, and TypeScript.",
            },
        ]
        github_repos = [
            {
                "name": "vercel/next.js",
                "url": "https://github.com/vercel/next.js",
                "description": "The React Framework for the Web",
            }
        ]
    elif "docker" in skill_lower or "kubernetes" in skill_lower or "devops" in skill_lower or "aws" in skill_lower:
        courses = [
            {
                "title": "Docker and Kubernetes: The Complete Guide",
                "platform": "Coursera / Udemy",
                "url": "https://www.coursera.org/learn/cloud-infrastructure",
                "type": "Course",
                "description": "Master containerization, pod orchestration, Helm charts, and CI/CD deployment pipelines.",
            },
            {
                "title": "AWS Certified Solutions Architect Training",
                "platform": "AWS Skill Builder",
                "url": "https://explore.skillbuilder.aws/",
                "type": "Official Certification Training",
                "description": "Official AWS training modules for cloud architecture and microservices design.",
            },
        ]
        github_repos = [
            {
                "name": "kubernetes/kubernetes",
                "url": "https://github.com/kubernetes/kubernetes",
                "description": "Production-Grade Container Scheduling and Management",
            }
        ]
    else:
        courses = [
            {
                "title": f"Mastering {clean_skill}: From Fundamentals to Advanced",
                "platform": "Coursera",
                "url": f"https://www.coursera.org/search?query={clean_skill.replace(' ', '%20')}",
                "type": "Specialization",
                "description": f"Professional specialization course covering key concepts, best practices, and hands-on projects in {clean_skill}.",
            },
            {
                "title": f"Hands-on {clean_skill} Deep Dive",
                "platform": "Udemy",
                "url": f"https://www.udemy.com/courses/search/?q={clean_skill.replace(' ', '%20')}",
                "type": "Course",
                "description": f"Practical project-based curriculum to build production skills in {clean_skill}.",
            },
        ]
        github_repos = [
            {
                "name": f"awesome-{clean_skill.lower().replace(' ', '-')}",
                "url": f"https://github.com/search?q=awesome+{clean_skill.replace(' ', '+')}",
                "description": f"Curated list of awesome {clean_skill} frameworks, libraries, software, and resources.",
            }
        ]

    return {
        "skill": clean_skill,
        "courses": courses,
        "github_repositories": github_repos,
        "total_resources": len(courses) + len(github_repos),
    }


def tool_fetch_certification_paths(role_name: str) -> dict[str, Any]:
    """Retrieve industry recognized certifications, prerequisites, and milestone pathways for a given job role."""
    clean_role = role_name.strip() if isinstance(role_name, str) else "Software Engineer"
    logger.info("Coach Agent fetching certification paths for role: %s", clean_role)

    role_lower = clean_role.lower()

    if "cloud" in role_lower or "devops" in role_lower or "infrastructure" in role_lower:
        certifications = [
            {
                "name": "AWS Certified Solutions Architect – Associate",
                "issuer": "Amazon Web Services",
                "difficulty": "Intermediate",
                "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
                "prerequisites": "Basic understanding of cloud concepts and distribution systems.",
            },
            {
                "name": "Certified Kubernetes Administrator (CKA)",
                "issuer": "Linux Foundation / CNCF",
                "difficulty": "Advanced",
                "url": "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
                "prerequisites": "Hands-on containerization experience and Linux CLI proficiency.",
            },
        ]
        pathway = ["Step 1: Linux & Docker Fundamentals", "Step 2: AWS Solutions Architect", "Step 3: CKA Kubernetes Certification"]
    elif "data" in role_lower or "ai" in role_lower or "machine learning" in role_lower:
        certifications = [
            {
                "name": "Google Cloud Professional Data Engineer",
                "issuer": "Google Cloud",
                "difficulty": "Advanced",
                "url": "https://cloud.google.com/learn/certification/data-engineer",
                "prerequisites": "Data processing, BigQuery, and SQL expertise.",
            },
            {
                "name": "AWS Certified Machine Learning – Specialty",
                "issuer": "Amazon Web Services",
                "difficulty": "Advanced",
                "url": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
                "prerequisites": "Python, ML algorithms, and cloud model deployment.",
            },
        ]
        pathway = ["Step 1: Advanced SQL & Python for Data Science", "Step 2: GCP Professional Data Engineer", "Step 3: AWS ML Specialty"]
    else:
        certifications = [
            {
                "name": f"Professional {clean_role} Certification",
                "issuer": "Industry Tech Alliance",
                "difficulty": "Intermediate",
                "url": f"https://www.google.com/search?q={clean_role.replace(' ', '+')}+professional+certification",
                "prerequisites": "Core domain fundamentals and practical project portfolio.",
            },
            {
                "name": "Meta Professional Certification",
                "issuer": "Meta / Coursera",
                "difficulty": "Beginner-Intermediate",
                "url": "https://www.coursera.org/meta",
                "prerequisites": "Basic programming and problem-solving skills.",
            },
        ]
        pathway = ["Step 1: Core Fundamentals & Capstone Project", "Step 2: Industry Professional Certification", "Step 3: Advanced Specialization"]

    return {
        "role": clean_role,
        "certifications": certifications,
        "recommended_path": pathway,
    }


# Gemini Function Declarations for Coach Agent
search_resources_decl = types.FunctionDeclaration(
    name="tool_search_learning_resources",
    description="Search for top courses, official documentation, and open-source repositories for missing technical skills or resume improvement areas.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "skill_name": types.Schema(
                type="STRING",
                description="The target skill or technology name to find learning resources for (e.g., Python, Docker, React, System Design)",
            ),
        },
        required=["skill_name"],
    ),
)

fetch_certs_decl = types.FunctionDeclaration(
    name="tool_fetch_certification_paths",
    description="Retrieve official industry certifications, prerequisites, and milestone learning pathways for a target job role.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "role_name": types.Schema(
                type="STRING",
                description="Target career role or job title (e.g., DevOps Engineer, Full Stack Developer, Data Scientist)",
            ),
        },
        required=["role_name"],
    ),
)

COACH_TOOLS = types.Tool(
    function_declarations=[search_resources_decl, fetch_certs_decl]
)


def execute_coach_tool(tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
    """Execute career coach tool function by name."""
    logger.info("Coach Agent executing tool '%s' with args: %s", tool_name, list(tool_args.keys()))
    if tool_name == "tool_search_learning_resources":
        return tool_search_learning_resources(
            skill_name=tool_args.get("skill_name", "Software Engineering")
        )
    elif tool_name == "tool_fetch_certification_paths":
        return tool_fetch_certification_paths(
            role_name=tool_args.get("role_name", "Software Engineer")
        )
    else:
        return {"error": "UNKNOWN_TOOL", "message": f"Unknown tool name: {tool_name}"}
