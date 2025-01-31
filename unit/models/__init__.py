import json

try:
    from typing import TypeVar, Generic, Union, Optional, Literal, List, Dict
except ImportError:
    from typing import TypeVar, Generic, Union, Optional, List, Dict
    from typing_extensions import Literal

from datetime import datetime, date

Occupation = Literal["ArchitectOrEngineer", "BusinessAnalystAccountantOrFinancialAdvisor",
                     "CommunityAndSocialServicesWorker", "ConstructionMechanicOrMaintenanceWorker", "Doctor",
                     "Educator", "EntertainmentSportsArtsOrMedia", "ExecutiveOrManager", "FarmerFishermanForester",
                     "FoodServiceWorker", "GigWorker", "HospitalityOfficeOrAdministrativeSupportWorker",
                     "HouseholdManager", "JanitorHousekeeperLandscaper", "Lawyer", "ManufacturingOrProductionWorker",
                     "MilitaryOrPublicSafety", "NurseHealthcareTechnicianOrHealthcareSupport",
                     "PersonalCareOrServiceWorker", "PilotDriverOperator", "SalesRepresentativeBrokerAgent",
                     "ScientistOrTechnologist", "Student"]
AnnualIncome = Literal["UpTo10k", "Between10kAnd25k", "Between25kAnd50k", "Between50kAnd100k", "Between100kAnd250k",
                       "Over250k"]
SourceOfIncome = Literal["EmploymentOrPayrollIncome", "PartTimeOrContractorIncome", "InheritancesAndGifts",
                         "PersonalInvestments", "BusinessOwnershipInterests", "GovernmentBenefits"]
Status = Literal["Approved", "Denied", "PendingReview"]
Title = Literal["CEO", "COO", "CFO", "President"]
EntityType = Literal["Corporation", "LLC", "Partnership"]
UseSelfieVerification = Literal["Never", "ReplaceIdentification"]


def to_camel_case(snake_str):
    components = snake_str.lstrip('_').split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


def extract_attributes(list_of_attributes, attributes):
    extracted_attributes = {}
    for a in list_of_attributes:
        if a in attributes:
            extracted_attributes[a] = attributes[a]

    return extracted_attributes


class UnitDTO(object):
    def to_dict(self):
        if type(self) is dict:
            return self
        else:
            v = vars(self)
            return dict((to_camel_case(k), val) for k, val in v.items() if val is not None)


class Relationship(UnitDTO):
    def __init__(self, _type: str, _id: str):
        self.type = _type
        self.id = _id

    def to_dict(self, nested: Optional[bool] = True):
        if nested:
            return {"data": {"type": self.type, "id": self.id}}
        else:
            return {"type": self.type, "id": self.id}


T = TypeVar('T')


class RelationshipArray(Generic[T], UnitDTO):
    def __init__(self, l: List[T]):
        relationships = []
        for r in l:
            if isinstance(r, Relationship):
                relationships.append(r)
            else:
                relationships.append(Relationship(r["type"], r["id"]))
        self.data = relationships

    def to_dict(self) -> Dict:
        return {"data": list(map(lambda r: r.to_dict(False), self.data))}

    @staticmethod
    def from_ids_array(type: str, ids: List[str]):
        return RelationshipArray(list(map(lambda id: Relationship(type, id), ids)))


class UnitResponse(Generic[T]):
    def __init__(self, data: Union[T, List[T]], included):
        self.data = data
        self.included = included

    @staticmethod
    def from_json_api(data: str):
        pass


class UnitRequest(object):
    def to_json_api(self) -> Dict:
        pass

    def vars_to_attributes_dict(self, ignore: List[str] = []) -> Dict:
        attributes = {}

        for k in self.__dict__:
            if k != "relationships" and k not in ignore:
                v = getattr(self, k)
                if v:
                    attributes[to_camel_case(k)] = v

        return attributes

    def to_payload(self, _type: str, relationships: Dict[str, Relationship] = None, ignore: List[str] = []) -> Dict:
        payload = {
            "data": {
                "type": _type,
                "attributes": self.vars_to_attributes_dict(ignore),
            }
        }

        if relationships:
            payload["data"]["relationships"] = relationships

        return payload

    def __repr__(self):
        return json.dumps(self.to_json_api())


class UnitParams(object):
    def to_dict(self) -> Dict:
        pass


class RawUnitObject(UnitDTO):
    def __init__(self, _id, _type, attributes, relationships):
        self.id = _id
        self.type = _type
        self.attributes = attributes
        self.relationships = relationships

    def to_dict(self):
        v = vars(self.attributes)
        return dict((to_camel_case(k), val) for k, val in v.items() if val is not None)


class UnitErrorPayload(object):
    def __init__(self, title: str, status: str, detail: Optional[str] = None, details: Optional[str] = None,
                 source: Optional[Dict] = None, code: Optional[str] = None, meta: Optional[Dict[str, object]] = None):
        self.title = title
        self.status = status
        self.detail = detail
        self.details = details
        self.source = source
        self.code = code
        self.meta = meta

    def __str__(self):
        return self.detail or self.title


class UnitError(object):
    def __init__(self, errors: List[UnitErrorPayload]):
        self.errors = errors

    @staticmethod
    def from_json_api(data: Dict):
        errors = []
        for err in data["errors"]:
            errors.append(
                UnitErrorPayload(err.get("title"), err.get("status"), err.get("detail", None),
                                 err.get("details", None), err.get("source", None), err.get("code", None),
                                 err.get("meta", None))
            )

        return UnitError(errors)

    def __str__(self):
        return json.dumps({"errors": [{"title": err.title, "status": err.status, "detail": err.detail,
                                       "details": err.details, "source": err.source, "code": err.code} for err in
                                      self.errors]})


class FullName(UnitDTO):
    def __init__(self, first: str, last: str):
        self.first = first
        self.last = last

    @staticmethod
    def from_json_api(data: Dict):
        return FullName(data.get("first"), data.get("last"))


# todo: Alex - use typing.Literal for multi accepted values (e.g country)
class Address(UnitDTO):
    def __init__(self, street: str, city: str, state: str, postal_code: str, country: str,
                 street2: Optional[str] = None):
        self.street = street
        self.street2 = street2
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country

    @staticmethod
    def from_json_api(data: Dict):
        if data:
            return Address(data.get("street"), data.get("city"), data.get("state"),
                           data.get("postalCode"), data.get("country"), data.get("street2", None))

        return None


class Phone(UnitDTO):
    def __init__(self, country_code: str, number: str):
        self.country_code = country_code
        self.number = number

    @staticmethod
    def from_json_api(data: Dict):
        return Phone(data.get("countryCode"), data.get("number"))


class EvaluationParams(object):
    def __init__(self, use_selfie_verification: Optional[UseSelfieVerification] = None,
                 require_id_verification: Optional[bool] = False):
        self.use_selfie_verification = use_selfie_verification
        self.require_id_verification = require_id_verification

    def to_json_api(self):
        return {
            "useSelfieVerification": self.use_selfie_verification,
            "requireIdVerification": self.require_id_verification,
        }

    @staticmethod
    def from_json_api(data: Dict):
        if data:
            return EvaluationParams(data.get("useSelfieVerification"), data.get("requireIdVerification"))

        return None


class BusinessContact(UnitDTO):
    def __init__(self, full_name: FullName, email: str, phone: Phone):
        self.full_name = full_name
        self.email = email
        self.phone = phone

    @staticmethod
    def from_json_api(data: Dict):
        return BusinessContact(FullName.from_json_api(data.get("fullName")), data.get("email"),
                               Phone.from_json_api(data.get("phone")))


class Officer(UnitDTO):
    def __init__(self, full_name: FullName, date_of_birth: date, address: Address, phone: Phone, email: str,
                 status: Optional[Status] = None, title: Optional[Title] = None, ssn: Optional[str] = None,
                 passport: Optional[str] = None, nationality: Optional[str] = None,
                 evaluation_params: Optional[EvaluationParams] = None, id_theft_score: Optional[str] = None,
                 occupation: Optional[Occupation] = None, annual_income: Optional[AnnualIncome] = None,
                 source_of_income: Optional[SourceOfIncome] = None):
        self.full_name = full_name
        self.date_of_birth = date_of_birth
        self.address = address
        self.phone = phone
        self.email = email
        self.status = status
        self.title = title
        self.ssn = ssn
        self.passport = passport
        self.nationality = nationality
        self.evaluation_params = evaluation_params
        self.id_theft_score = id_theft_score
        self.occupation = occupation
        self.annual_income = annual_income
        self.source_of_income = source_of_income

    @staticmethod
    def from_json_api(data: Dict):
        return Officer(data.get("fullName"), data.get("dateOfBirth"), data.get("address"), data.get("phone"),
                       data.get("email"), data.get("status"), data.get("title"), data.get("ssn"), data.get("passport"),
                       data.get("nationality"), EvaluationParams.from_json_api(data.get("evaluationParams")),
                       data.get("idTheftScore"), data.get("occupation"), data.get("annualIncome"),
                       data.get("sourceOfIncome"))


class BeneficialOwner(UnitDTO):
    def __init__(self, full_name: FullName, date_of_birth: date, address: Address, phone: Phone, email: str,
                 status: Optional[Status] = None, ssn: Optional[str] = None, passport: Optional[str] = None,
                 nationality: Optional[str] = None, percentage: Optional[int] = None,
                 evaluation_params: Optional[EvaluationParams] = None, id_theft_score: Optional[str] = None,
                 occupation: Optional[Occupation] = None, annual_income: Optional[AnnualIncome] = None,
                 source_of_income: Optional[SourceOfIncome] = None):
        self.full_name = full_name
        self.date_of_birth = date_of_birth
        self.address = address
        self.phone = phone
        self.email = email
        self.status = status
        self.ssn = ssn
        self.passport = passport
        self.nationality = nationality
        self.percentage = percentage
        self.evaluation_params = evaluation_params
        self.id_theft_score = id_theft_score
        self.occupation = occupation
        self.annual_income = annual_income
        self.source_of_income = source_of_income

    @staticmethod
    def create(data: Dict):
        return BeneficialOwner(data.get("fullName"), data.get("dateOfBirth"), data.get("address"),
                               data.get("phone"), data.get("email"), data.get("status"), data.get("ssn"),
                               data.get("passport"), data.get("nationality"), data.get("percentage"),
                               EvaluationParams.from_json_api(data.get("evaluationParams")), data.get("idTheftScore"),
                               data.get("occupation"), data.get("annualIncome"), data.get("sourceOfIncome"))

    @staticmethod
    def from_json_api(l: Union[List, Dict]):
        if isinstance(l, list):
            beneficial_owners = []
            for data in l:
                beneficial_owners.append(BeneficialOwner.create(data))
            return beneficial_owners
        else:
            return BeneficialOwner.create(l)


class BeneficialOwnerDTO(UnitDTO):
    def __init__(self, _id: str, _type: str, attributes: BeneficialOwner, relationships: Dict[str, Relationship]):
        self.id = _id
        self.type = _type
        self.attributes = attributes
        self.relationships = relationships

    @staticmethod
    def from_json_api(_id, _type, attributes, relationships):
        return BeneficialOwnerDTO(_id, _type, BeneficialOwner.from_json_api(attributes), relationships)


class AuthorizedUser(UnitDTO):
    def __init__(self, full_name: FullName, email: str, phone: Phone, jwt_subject: Optional[str]):
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.jwt_subject = jwt_subject

    @staticmethod
    def from_json_api(data):
        if data is None:
            return None

        if data is []:
            return []

        if type(data) is dict:
            return AuthorizedUser(FullName.from_json_api(data.get("fullName")), data.get("email"),
                                  Phone.from_json_api(data.get("phone")), data.get("jwtSubject"))

        return [AuthorizedUser(FullName.from_json_api(d.get("fullName")), d.get("email"),
                               Phone.from_json_api(d.get("phone")), d.get("jwtSubject")) for d in data]


class WireCounterparty(UnitDTO):
    def __init__(self, routing_number: str, account_number: str, name: str, address: Address):
        self.routing_number = routing_number
        self.account_number = account_number
        self.name = name
        self.address = address

    @staticmethod
    def from_json_api(data: Dict):
        return WireCounterparty(data["routingNumber"], data["accountNumber"], data["name"],
                                Address.from_json_api(data["address"]))


class Counterparty(UnitDTO):
    def __init__(self, routing_number: str, account_number: str, account_type: str, name: str):
        self.routing_number = routing_number
        self.account_number = account_number
        self.account_type = account_type
        self.name = name

    @staticmethod
    def from_json_api(data: Dict):
        return Counterparty(data["routingNumber"], data["accountNumber"], data["accountType"], data["name"])


class Coordinates(UnitDTO):
    def __init__(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude

    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return Coordinates(data["longitude"], data["latitude"])


class Merchant(UnitDTO):
    def __init__(self, name: str, _type: int, category: str, location: Optional[str], _id: Optional[str]):
        self.name = name
        self.type = _type
        self.category = category
        self.location = location
        self.id = _id

    @staticmethod
    def from_json_api(data: Dict):
        if data:
            return Merchant(data["name"], data["type"], data["category"], data.get("location"), data.get("id"))

        return None


class CardLevelLimits(UnitDTO):
    def __init__(self, daily_withdrawal: int, daily_purchase: int, monthly_withdrawal: int, monthly_purchase: int):
        self.daily_withdrawal = daily_withdrawal
        self.daily_purchase = daily_purchase
        self.monthly_withdrawal = monthly_withdrawal
        self.monthly_purchase = monthly_purchase

    @staticmethod
    def from_json_api(data: Dict):
        return CardLevelLimits(data["dailyWithdrawal"], data["dailyPurchase"], data["monthlyWithdrawal"],
                               data["monthlyPurchase"])


class CardTotals(UnitDTO):
    def __init__(self, withdrawals: int, deposits: int, purchases: int):
        self.withdrawals = withdrawals
        self.deposits = deposits
        self.purchases = purchases

    @staticmethod
    def from_json_api(data: Dict):
        return CardTotals(data["withdrawals"], data["deposits"], data["purchases"])


class DeviceFingerprint(UnitDTO):
    def __init__(self, value: str, provider: str = "iovation"):
        self.value = value
        self.provider = provider

    def to_json_api(self):
        return {
            "value": self.value,
            "provider": self.provider,
        }

    @classmethod
    def from_json_api(cls, data: Dict):
        return cls(value=data["value"], provider=data["provider"])


class CheckCounterparty(object):
    def __init__(self, routing_number: str, account_number: str, name: str):
        self.routing_number = routing_number
        self.account_number = account_number
        self.name = name

    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return CheckCounterparty(data["routingNumber"], data["accountNumber"], data["name"])


class BaseIndividual(UnitDTO):
    def __init__(self, full_name: FullName, date_of_birth: date, ssn: str, email: str, phone: Phone, address: Address):
        self.full_name = full_name
        self.date_of_birth = date_of_birth
        self.ssn = ssn
        self.email = email
        self.phone = phone
        self.address = address


class Grantor(BaseIndividual):
    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return Grantor(FullName.from_json_api(data["fullName"]), data["dateOfBirth"], data["ssn"], data["email"],
                       Phone.from_json_api(data["phone"]), Address.from_json_api(data["address"]))


class Trustee(BaseIndividual):
    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return Trustee(FullName.from_json_api(data["fullName"]), data["dateOfBirth"], data["ssn"], data["email"],
                       Phone.from_json_api(data["phone"]), Address.from_json_api(data["address"]))


class TrustContact(UnitDTO):
    def __init__(self, full_name: FullName, email: str, phone: Phone, address: Address, jwt_subject: Optional[str]):
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.address = address
        self.jwt_subject = jwt_subject

    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return TrustContact(FullName.from_json_api(data["fullName"]), data["email"], Phone.from_json_api(data["phone"]),
                            Address.from_json_api(data["address"]), data.get("jwtSubject"))


class Agent(BaseIndividual):
    def __init__(self, status: str, full_name: FullName, ssn: Optional[str], passport: Optional[str],
                 nationality: Optional[str], date_of_birth: date, email: str, phone: Phone, address: Address,
                 jwt_subject: Optional[str]):
        super().__init__(full_name, date_of_birth, ssn, email, phone, address)
        self.status = status
        self.passport = passport
        self.nationality = nationality
        self.jwt_subject = jwt_subject

    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return Agent(data["status"], FullName.from_json_api(data["fullName"]), data.get("ssn"), data.get("passport"),
                     data.get("nationality"), data["dateOfBirth"], data["email"], Phone.from_json_api(data["phone"]),
                     Address.from_json_api(data["address"]), data.get("jwtSubject"))


class Beneficiary(UnitDTO):
    def __init__(self, full_name: FullName, date_of_birth: date):
        self.full_name = full_name
        self.date_of_birth = date_of_birth

    @staticmethod
    def from_json_api(data: Dict):
        if not data:
            return None

        return Beneficiary(FullName.from_json_api(data["fullName"]), data.get("dateOfBirth"))
