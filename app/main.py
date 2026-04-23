from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import Body, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.models import (
    Organization,
    OrganizationCreate,
    OrganizationList,
    OrganizationUpdate,
    ProblemDetails,
    Question,
    QuestionCreate,
    QuestionList,
    QuestionOption,
    QuestionSummary,
    QuestionType,
    QuestionUpdate,
    Response as SurveyResponse,
    ResponseCreate,
    ResponseList,
    Survey,
    SurveyCreate,
    SurveyForm,
    SurveyList,
    SurveyStatus,
    SurveySummaryReport,
    SurveyUpdate,
    NpsSummary,
)


ADMIN_PROBLEM_RESPONSES = {
    400: {"model": ProblemDetails, "description": "Bad request"},
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    404: {"model": ProblemDetails, "description": "Resource not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation error"},
}


PUBLIC_PROBLEM_RESPONSES = {
    400: {"model": ProblemDetails, "description": "Bad request"},
    404: {"model": ProblemDetails, "description": "Resource not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation error"},
}


PUBLIC_PATH_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/surveys/slug/",
)


PUBLIC_PATHS = {
    "/",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
    "/health",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_problem(status_code: int, title: str, detail: str, instance: Optional[str] = None) -> JSONResponse:
    payload = ProblemDetails(
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(),
        media_type="application/problem+json",
    )


def is_public_request_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PATH_PREFIXES)


def is_valid_admin_token(authorization_header: Optional[str]) -> bool:
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return False
    token = authorization_header[len("Bearer ") :].strip()
    return bool(settings.admin_bearer_token) and token == settings.admin_bearer_token


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "MVP backend for collecting customer feedback. "
        "Survey access is controlled by the isPublic property instead of a separate public URL namespace."
    ),
    openapi_version=settings.openapi_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    if is_public_request_path(request.url.path):
        return await call_next(request)

    if is_valid_admin_token(request.headers.get("Authorization")):
        return await call_next(request)

    return to_problem(
        status.HTTP_401_UNAUTHORIZED,
        "Unauthorized",
        "Admin endpoints require a valid bearer token.",
        str(request.url),
    )


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return to_problem(exc.status_code, "HTTP Error", detail, str(request.url))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = "; ".join(error["msg"] for error in exc.errors()) or "Validation failed."
    response = to_problem(status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation Error", detail, str(request.url))
    response.body = response.body
    return response


def create_demo_state() -> Dict[str, Any]:
    now = utcnow()
    organization_id = UUID("11111111-1111-1111-1111-111111111111")
    survey_id = UUID("22222222-2222-2222-2222-222222222222")
    question_one_id = UUID("33333333-3333-3333-3333-333333333331")
    question_two_id = UUID("33333333-3333-3333-3333-333333333332")
    question_three_id = UUID("33333333-3333-3333-3333-333333333333")
    response_id = UUID("44444444-4444-4444-4444-444444444444")

    organizations = {
        organization_id: {
            "id": organization_id,
            "name": "Demo Company",
            "slug": "demo-company",
            "createdAt": now,
            "updatedAt": now,
        }
    }

    surveys = {
        survey_id: {
            "id": survey_id,
            "organizationId": organization_id,
            "title": "Store visit feedback",
            "description": "Sample published survey for Swagger UI exploration.",
            "slug": "store-visit-feedback",
            "status": SurveyStatus.published,
            "isPublic": True,
            "isAnonymous": True,
            "createdAt": now,
            "updatedAt": now,
            "publishedAt": now,
            "archivedAt": None,
            "deletedAt": None,
        }
    }

    questions = {
        question_one_id: {
            "id": question_one_id,
            "surveyId": survey_id,
            "type": QuestionType.rating,
            "title": "How satisfied were you with your visit?",
            "description": None,
            "required": True,
            "order": 1,
            "options": [],
            "createdAt": now,
            "updatedAt": now,
        },
        question_two_id: {
            "id": question_two_id,
            "surveyId": survey_id,
            "type": QuestionType.nps,
            "title": "How likely are you to recommend us?",
            "description": None,
            "required": True,
            "order": 2,
            "options": [],
            "createdAt": now,
            "updatedAt": now,
        },
        question_three_id: {
            "id": question_three_id,
            "surveyId": survey_id,
            "type": QuestionType.single_choice,
            "title": "What was the main reason for your visit?",
            "description": None,
            "required": False,
            "order": 3,
            "options": [
                QuestionOption(value="support", label="Support").model_dump(),
                QuestionOption(value="purchase", label="Purchase").model_dump(),
                QuestionOption(value="return", label="Return").model_dump(),
            ],
            "createdAt": now,
            "updatedAt": now,
        },
    }

    responses = {
        response_id: {
            "id": response_id,
            "surveyId": survey_id,
            "submittedAt": now,
            "respondentName": None,
            "email": None,
            "phone": None,
            "orderId": None,
            "serviceAgent": None,
            "channel": "web",
            "consentGiven": True,
            "answers": [
                {"questionId": question_one_id, "value": 5},
                {"questionId": question_two_id, "value": 9},
                {"questionId": question_three_id, "value": "purchase"},
            ],
        }
    }

    return {
        "organizations": organizations,
        "surveys": surveys,
        "questions": questions,
        "responses": responses,
    }


STATE = create_demo_state()


def list_questions_for_survey(survey_id: UUID) -> List[Question]:
    questions = [Question(**question) for question in STATE["questions"].values() if question["surveyId"] == survey_id]
    return sorted(questions, key=lambda item: item.order)


def get_organization_or_404(organization_id: UUID) -> Dict[str, Any]:
    organization = STATE["organizations"].get(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return organization


def get_survey_or_404(survey_id: UUID, include_deleted: bool = False) -> Dict[str, Any]:
    survey = STATE["surveys"].get(survey_id)
    if not survey or (survey["deletedAt"] and not include_deleted):
        raise HTTPException(status_code=404, detail="Survey not found.")
    return survey


def get_question_or_404(survey_id: UUID, question_id: UUID) -> Dict[str, Any]:
    question = STATE["questions"].get(question_id)
    if not question or question["surveyId"] != survey_id:
        raise HTTPException(status_code=404, detail="Question not found.")
    return question


def get_response_or_404(response_id: UUID) -> Dict[str, Any]:
    response = STATE["responses"].get(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found.")
    return response


def ensure_unique_slug(resources: Dict[UUID, Dict[str, Any]], slug: str, current_id: Optional[UUID] = None) -> None:
    for resource_id, resource in resources.items():
        if current_id == resource_id:
            continue
        if resource["slug"] == slug:
            raise HTTPException(status_code=409, detail="Slug already exists.")


def get_accessible_survey_by_slug_or_404(slug: str) -> Dict[str, Any]:
    for survey in STATE["surveys"].values():
        if survey["slug"] != slug:
            continue
        if survey["deletedAt"] is not None:
            continue
        if survey["status"] == SurveyStatus.published and survey["isPublic"]:
            return survey
        break
    raise HTTPException(status_code=404, detail="Published survey not found.")


def validate_question_options(question_type: QuestionType, options: List[Dict[str, str]]) -> None:
    if question_type in {QuestionType.single_choice, QuestionType.multiple_choice} and not options:
        raise HTTPException(status_code=422, detail="Choice questions require at least one option.")
    if question_type not in {QuestionType.single_choice, QuestionType.multiple_choice} and options:
        raise HTTPException(status_code=422, detail="Only choice questions may define options.")


def validate_answer(question: Dict[str, Any], value: Any) -> None:
    question_type = question["type"]
    options = {option["value"] for option in question["options"]}

    if question_type in {QuestionType.text, QuestionType.textarea}:
        if not isinstance(value, str):
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' expects a string.")
        if question["required"] and not value.strip():
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' requires a value.")
    elif question_type == QuestionType.rating:
        if not isinstance(value, int) or not 1 <= value <= 5:
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' expects an integer from 1 to 5.")
    elif question_type == QuestionType.nps:
        if not isinstance(value, int) or not 0 <= value <= 10:
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' expects an integer from 0 to 10.")
    elif question_type == QuestionType.boolean:
        if not isinstance(value, bool):
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' expects a boolean.")
    elif question_type == QuestionType.single_choice:
        if not isinstance(value, str) or value not in options:
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' expects one allowed option.")
    elif question_type == QuestionType.multiple_choice:
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' expects an array of strings.")
        if any(item not in options for item in value):
            raise HTTPException(status_code=422, detail=f"Question '{question['title']}' contains unsupported options.")


def validate_response_payload(survey_id: UUID, payload: ResponseCreate) -> None:
    survey_questions = {question.id: question for question in list_questions_for_survey(survey_id)}
    provided_questions = {answer.questionId for answer in payload.answers}

    if len(provided_questions) != len(payload.answers):
        raise HTTPException(status_code=422, detail="Duplicate answers for the same question are not allowed.")

    for question in survey_questions.values():
        if question.required and question.id not in provided_questions:
            raise HTTPException(status_code=422, detail=f"Missing required answer for '{question.title}'.")

    for answer in payload.answers:
        question = survey_questions.get(answer.questionId)
        if not question:
            raise HTTPException(status_code=422, detail="Answer references a question outside the survey.")
        validate_answer(question.model_dump() if hasattr(question, "model_dump") else question.dict(), answer.value)


def paginate(items: List[Any], page: int, page_size: int) -> List[Any]:
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/organizations", response_model=OrganizationList, tags=["Organizations"], responses=ADMIN_PROBLEM_RESPONSES)
def list_organizations(page: int = Query(default=1, ge=1), pageSize: int = Query(default=20, ge=1, le=100)) -> OrganizationList:
    organizations = [Organization(**item) for item in STATE["organizations"].values()]
    organizations.sort(key=lambda item: item.createdAt, reverse=True)
    return OrganizationList(items=paginate(organizations, page, pageSize), page=page, pageSize=pageSize, total=len(organizations))


@app.post(
    "/organizations",
    response_model=Organization,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"],
    responses=ADMIN_PROBLEM_RESPONSES,
)
def create_organization(payload: OrganizationCreate) -> Organization:
    ensure_unique_slug(STATE["organizations"], payload.slug)
    now = utcnow()
    organization_id = uuid4()
    item = {
        "id": organization_id,
        "name": payload.name,
        "slug": payload.slug,
        "createdAt": now,
        "updatedAt": now,
    }
    STATE["organizations"][organization_id] = item
    return Organization(**item)


@app.get("/organizations/{organizationId}", response_model=Organization, tags=["Organizations"], responses=ADMIN_PROBLEM_RESPONSES)
def get_organization(organizationId: UUID) -> Organization:
    return Organization(**get_organization_or_404(organizationId))


@app.patch("/organizations/{organizationId}", response_model=Organization, tags=["Organizations"], responses=ADMIN_PROBLEM_RESPONSES)
def update_organization(organizationId: UUID, payload: OrganizationUpdate) -> Organization:
    organization = get_organization_or_404(organizationId)
    update_data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    if "slug" in update_data:
        ensure_unique_slug(STATE["organizations"], update_data["slug"], organizationId)
    organization.update(update_data)
    organization["updatedAt"] = utcnow()
    return Organization(**organization)


@app.get("/surveys", response_model=SurveyList, tags=["Surveys"], responses=ADMIN_PROBLEM_RESPONSES)
def list_surveys(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    organizationId: Optional[UUID] = None,
    status_filter: Optional[SurveyStatus] = Query(default=None, alias="status"),
    search: Optional[str] = None,
) -> SurveyList:
    surveys = [Survey(**item) for item in STATE["surveys"].values() if item["deletedAt"] is None]
    if organizationId:
        surveys = [item for item in surveys if item.organizationId == organizationId]
    if status_filter:
        surveys = [item for item in surveys if item.status == status_filter]
    if search:
        needle = search.lower()
        surveys = [item for item in surveys if needle in item.title.lower() or needle in (item.description or "").lower()]
    surveys.sort(key=lambda item: item.createdAt, reverse=True)
    return SurveyList(items=paginate(surveys, page, pageSize), page=page, pageSize=pageSize, total=len(surveys))


@app.post("/surveys", response_model=Survey, status_code=status.HTTP_201_CREATED, tags=["Surveys"], responses=ADMIN_PROBLEM_RESPONSES)
def create_survey(payload: SurveyCreate) -> Survey:
    get_organization_or_404(payload.organizationId)
    ensure_unique_slug(STATE["surveys"], payload.slug)
    now = utcnow()
    survey_id = uuid4()
    published_at = now if payload.status == SurveyStatus.published else None
    archived_at = now if payload.status == SurveyStatus.archived else None
    item = {
        "id": survey_id,
        "organizationId": payload.organizationId,
        "title": payload.title,
        "description": payload.description,
        "slug": payload.slug,
        "status": payload.status,
        "isPublic": payload.isPublic,
        "isAnonymous": payload.isAnonymous,
        "createdAt": now,
        "updatedAt": now,
        "publishedAt": published_at,
        "archivedAt": archived_at,
        "deletedAt": None,
    }
    STATE["surveys"][survey_id] = item
    return Survey(**item)


@app.get("/surveys/{surveyId}", response_model=Survey, tags=["Surveys"], responses=ADMIN_PROBLEM_RESPONSES)
def get_survey(surveyId: UUID) -> Survey:
    return Survey(**get_survey_or_404(surveyId))


@app.patch("/surveys/{surveyId}", response_model=Survey, tags=["Surveys"], responses=ADMIN_PROBLEM_RESPONSES)
def update_survey(surveyId: UUID, payload: SurveyUpdate) -> Survey:
    survey = get_survey_or_404(surveyId)
    update_data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    if "slug" in update_data:
        ensure_unique_slug(STATE["surveys"], update_data["slug"], surveyId)
    if "status" in update_data:
        if update_data["status"] == SurveyStatus.published and survey["publishedAt"] is None:
            survey["publishedAt"] = utcnow()
        if update_data["status"] == SurveyStatus.archived:
            survey["archivedAt"] = utcnow()
    survey.update(update_data)
    survey["updatedAt"] = utcnow()
    return Survey(**survey)


@app.delete("/surveys/{surveyId}", status_code=status.HTTP_204_NO_CONTENT, tags=["Surveys"], responses=ADMIN_PROBLEM_RESPONSES)
def delete_survey(surveyId: UUID) -> Response:
    survey = get_survey_or_404(surveyId)
    survey["deletedAt"] = utcnow()
    survey["status"] = SurveyStatus.archived
    survey["archivedAt"] = survey["deletedAt"]
    survey["updatedAt"] = survey["deletedAt"]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/surveys/{surveyId}/questions", response_model=QuestionList, tags=["Questions"], responses=ADMIN_PROBLEM_RESPONSES)
def list_questions(surveyId: UUID) -> QuestionList:
    get_survey_or_404(surveyId)
    return QuestionList(items=list_questions_for_survey(surveyId))


@app.post("/surveys/{surveyId}/questions", response_model=Question, status_code=status.HTTP_201_CREATED, tags=["Questions"], responses=ADMIN_PROBLEM_RESPONSES)
def create_question(surveyId: UUID, payload: QuestionCreate) -> Question:
    get_survey_or_404(surveyId)
    options = [option.model_dump() if hasattr(option, "model_dump") else option.dict() for option in payload.options]
    validate_question_options(payload.type, options)
    now = utcnow()
    question_id = uuid4()
    item = {
        "id": question_id,
        "surveyId": surveyId,
        "type": payload.type,
        "title": payload.title,
        "description": payload.description,
        "required": payload.required,
        "order": payload.order,
        "options": options,
        "createdAt": now,
        "updatedAt": now,
    }
    STATE["questions"][question_id] = item
    return Question(**item)


@app.get("/surveys/{surveyId}/questions/{questionId}", response_model=Question, tags=["Questions"], responses=ADMIN_PROBLEM_RESPONSES)
def get_question(surveyId: UUID, questionId: UUID) -> Question:
    return Question(**get_question_or_404(surveyId, questionId))


@app.patch("/surveys/{surveyId}/questions/{questionId}", response_model=Question, tags=["Questions"], responses=ADMIN_PROBLEM_RESPONSES)
def update_question(surveyId: UUID, questionId: UUID, payload: QuestionUpdate) -> Question:
    question = get_question_or_404(surveyId, questionId)
    update_data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    question_type = update_data.get("type", question["type"])
    options = update_data.get("options", question["options"])
    if update_data.get("options") is not None:
        options = [option.model_dump() if hasattr(option, "model_dump") else option.dict() for option in update_data["options"]]
        update_data["options"] = options
    validate_question_options(question_type, options)
    question.update(update_data)
    question["updatedAt"] = utcnow()
    return Question(**question)


@app.delete("/surveys/{surveyId}/questions/{questionId}", status_code=status.HTTP_204_NO_CONTENT, tags=["Questions"], responses=ADMIN_PROBLEM_RESPONSES)
def delete_question(surveyId: UUID, questionId: UUID) -> Response:
    get_question_or_404(surveyId, questionId)
    del STATE["questions"][questionId]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/surveys/{surveyId}/responses", response_model=ResponseList, tags=["Responses"], responses=ADMIN_PROBLEM_RESPONSES)
def list_responses(
    surveyId: UUID,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    submittedFrom: Optional[datetime] = None,
    submittedTo: Optional[datetime] = None,
    channel: Optional[str] = None,
) -> ResponseList:
    get_survey_or_404(surveyId)
    responses = [SurveyResponse(**item) for item in STATE["responses"].values() if item["surveyId"] == surveyId]
    if submittedFrom:
        responses = [item for item in responses if item.submittedAt >= submittedFrom]
    if submittedTo:
        responses = [item for item in responses if item.submittedAt <= submittedTo]
    if channel:
        responses = [item for item in responses if item.channel == channel]
    responses.sort(key=lambda item: item.submittedAt, reverse=True)
    return ResponseList(items=paginate(responses, page, pageSize), page=page, pageSize=pageSize, total=len(responses))


@app.get("/responses/{responseId}", response_model=SurveyResponse, tags=["Responses"], responses=ADMIN_PROBLEM_RESPONSES)
def get_response(responseId: UUID) -> SurveyResponse:
    return SurveyResponse(**get_response_or_404(responseId))


@app.get("/reports/surveys/{surveyId}/summary", response_model=SurveySummaryReport, tags=["Reports"], responses=ADMIN_PROBLEM_RESPONSES)
def get_survey_summary(surveyId: UUID) -> SurveySummaryReport:
    get_survey_or_404(surveyId)
    questions = list_questions_for_survey(surveyId)
    responses = [SurveyResponse(**item) for item in STATE["responses"].values() if item["surveyId"] == surveyId]

    rating_values: List[int] = []
    nps_values: List[int] = []
    question_summaries: List[QuestionSummary] = []

    for question in questions:
        values = []
        for response in responses:
            for answer in response.answers:
                if answer.questionId == question.id:
                    values.append(answer.value)

        summary_kwargs: Dict[str, Any] = {
            "questionId": question.id,
            "title": question.title,
            "type": question.type,
            "responseCount": len(values),
            "valueCounts": {},
        }

        if question.type == QuestionType.rating:
            numeric_values = [int(value) for value in values]
            rating_values.extend(numeric_values)
            summary_kwargs["averageScore"] = round(sum(numeric_values) / len(numeric_values), 2) if numeric_values else None
        elif question.type == QuestionType.nps:
            numeric_values = [int(value) for value in values]
            nps_values.extend(numeric_values)
            summary_kwargs["averageScore"] = round(sum(numeric_values) / len(numeric_values), 2) if numeric_values else None
        else:
            counter = Counter(str(value) for value in values)
            summary_kwargs["valueCounts"] = dict(counter)

        question_summaries.append(QuestionSummary(**summary_kwargs))

    nps_summary = None
    if nps_values:
        promoters = sum(1 for value in nps_values if value >= 9)
        passives = sum(1 for value in nps_values if 7 <= value <= 8)
        detractors = sum(1 for value in nps_values if value <= 6)
        score = ((promoters - detractors) / len(nps_values)) * 100
        nps_summary = NpsSummary(
            totalResponses=len(nps_values),
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            score=round(score, 2),
        )

    average_rating = round(sum(rating_values) / len(rating_values), 2) if rating_values else None
    return SurveySummaryReport(
        surveyId=surveyId,
        responseCount=len(responses),
        averageRating=average_rating,
        nps=nps_summary,
        questionSummaries=question_summaries,
    )


@app.get("/surveys/slug/{slug}", response_model=SurveyForm, tags=["Survey Access"], responses=PUBLIC_PROBLEM_RESPONSES)
def get_survey_by_slug(slug: str) -> SurveyForm:
    survey = get_accessible_survey_by_slug_or_404(slug)
    return SurveyForm(
        id=survey["id"],
        title=survey["title"],
        description=survey["description"],
        slug=survey["slug"],
        status=survey["status"],
        isPublic=survey["isPublic"],
        questions=list_questions_for_survey(survey["id"]),
    )


@app.post(
    "/surveys/slug/{slug}/responses",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Survey Access"],
    responses=PUBLIC_PROBLEM_RESPONSES,
)
def submit_survey_response(
    slug: str,
    payload: ResponseCreate = Body(
        ...,
        examples=[
            {
                "channel": "web",
                "consentGiven": True,
                "answers": [
                    {"questionId": "33333333-3333-3333-3333-333333333331", "value": 5},
                    {"questionId": "33333333-3333-3333-3333-333333333332", "value": 10},
                    {"questionId": "33333333-3333-3333-3333-333333333333", "value": "purchase"},
                ],
            }
        ],
    ),
) -> SurveyResponse:
    survey = get_accessible_survey_by_slug_or_404(slug)

    validate_response_payload(survey["id"], payload)

    response_id = uuid4()
    response_item = {
        "id": response_id,
        "surveyId": survey["id"],
        "submittedAt": utcnow(),
        "respondentName": payload.respondentName,
        "email": payload.email,
        "phone": payload.phone,
        "orderId": payload.orderId,
        "serviceAgent": payload.serviceAgent,
        "channel": payload.channel,
        "consentGiven": payload.consentGiven,
        "answers": [
            answer.model_dump() if hasattr(answer, "model_dump") else answer.dict() for answer in payload.answers
        ],
    }
    STATE["responses"][response_id] = response_item
    return SurveyResponse(**response_item)


def custom_openapi() -> Dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = settings.openapi_version
    openapi_schema["servers"] = settings.openapi_servers
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Bearer token used for admin endpoints. Local development defaults to ADMIN_BEARER_TOKEN=local-admin-token.",
    }

    for path, methods in openapi_schema.get("paths", {}).items():
        if path in {"/health", "/surveys/slug/{slug}", "/surveys/slug/{slug}/responses"}:
            continue
        for method, operation in methods.items():
            if method.lower() in {"get", "post", "patch", "delete"}:
                operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
