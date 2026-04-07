from abc import ABC, abstractmethod

from fastrecvsms.models import Balance, Order, ServiceInfo


class SMSProvider(ABC):
    name: str

    @abstractmethod
    def __init__(self, api_key: str): ...

    @abstractmethod
    def get_balance(self) -> Balance: ...

    @abstractmethod
    def get_services(self, country: str = "any") -> list[ServiceInfo]: ...

    @abstractmethod
    def buy_number(self, service: str, country: str = "any", operator: str = "any") -> Order: ...

    @abstractmethod
    def check_order(self, order_id: int) -> Order: ...

    @abstractmethod
    def cancel_order(self, order_id: int) -> bool: ...

    @abstractmethod
    def finish_order(self, order_id: int) -> bool: ...
