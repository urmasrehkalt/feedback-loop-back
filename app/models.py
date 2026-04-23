from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class SurveyStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class QuestionType(str, Enum):
    text = "text"
    textarea = "textarea"
    rating = "rating"
    nps = "nps"
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    boolean = "boolean"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: Optional[str] = None


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")


class Organization(OrganizationBase):
    id: UUID
    createdAt: datetime
    updatedAt: datetime


class OrganizationList(BaseModel):
    items: List[Organization]
    page: int
    pageSize: int
    total: int


class SurveyBase(BaseModel):
    organizationId: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    slug: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")
    status: SurveyStatus = SurveyStatus.draft
    isPublic: bool = False
    isAnonymous: bool = True


class SurveyCreate(SurveyBase):
    pass


class SurveyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")
    status: Optional[SurveyStatus] = None
    isPublic: Optional[bool] = None
    isAnonymous: Optional[bool] = None


class Survey(BaseModel):
    id: UUID
    organizationId: UUID
    title: str
    description: Optional[str] = None
    slug: str
    status: SurveyStatus
    isPublic: bool
    isAnonymous: bool
    createdAt: datetime
    updatedAt: datetime
    publishedAt: Optional[datetime] = None
    archivedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None


class SurveyList(BaseModel):
    items: List[Survey]
    page: int
    pageSize: int
    total: int


class QuestionOption(BaseModel):
    value: str = Field(..., min_length=1, max_length=120)
    label: str = Field(..., min_length=1, max_length=120)


class QuestionBase(BaseModel):
    type: QuestionType
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    required: bool = False
    order: int = Field(default=0, ge=0)
    options: List[QuestionOption] = Field(default_factory=list)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    type: Optional[QuestionType] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    required: Optional[bool] = None
    order: Optional[int] = Field(default=None, ge=0)
    options: Optional[List[QuestionOption]] = None


class Question(BaseModel):
    id: UUID
    surveyId: UUID
    type: QuestionType
    title: str
    description: Optional[str] = None
    required: bool
    order: int
    options: List[QuestionOption] = Field(default_factory=list)
    createdAt: datetime
    updatedAt: datetime


class QuestionList(BaseModel):
    items: List[Question]


AnswerValue = Union[str, int, float, bool, List[str]]


class AnswerSubmission(BaseModel):
    questionId: UUID
    value: AnswerValue


class ResponseCreate(BaseModel):
    respondentName: Optional[str] = Field(default=None, max_length=120)
    email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = Field(default=None, max_length=40)
    orderId: Optional[str] = Field(default=None, max_length=120)
    serviceAgent: Optional[str] = Field(default=None, max_length=120)
    channel: Optional[str] = Field(default=None, max_length=50)
    consentGiven: bool = False
    answers: List[AnswerSubmission] = Field(default_factory=list, min_length=1)


class Response(BaseModel):
    id: UUID
    surveyId: UUID
    submittedAt: datetime
    respondentName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    orderId: Optional[str] = None
    serviceAgent: Optional[str] = None
    channel: Optional[str] = None
    consentGiven: bool = False
    answers: List[AnswerSubmission]


class ResponseList(BaseModel):
    items: List[Response]
    page: int
    pageSize: int
    total: int


class SurveyForm(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    slug: str
    status: SurveyStatus
    isPublic: bool
    questions: List[Question]


class QuestionSummary(BaseModel):
    questionId: UUID
    title: str
    type: QuestionType
    responseCount: int
    averageScore: Optional[float] = None
    valueCounts: Dict[str, int] = Field(default_factory=dict)


class NpsSummary(BaseModel):
    totalResponses: int
    promoters: int
    passives: int
    detractors: int
    score: Optional[float] = None


class SurveySummaryReport(BaseModel):
    surveyId: UUID
    responseCount: int
    averageRating: Optional[float] = None
    nps: Optional[NpsSummary] = None
    questionSummaries: List[QuestionSummary]
