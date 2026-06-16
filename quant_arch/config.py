from pydantic import BaseModel, Field

class RiskConfig(BaseModel):
    max_drawdown: float = Field(0.12)
    min_sharpe: float = Field(0.5)
    min_signal_ev: float = Field(0.01)
    max_position: float = Field(1.0)

class ModelConfig(BaseModel):
    monte_carlo_paths: int = Field(3000)
    confidence_alpha: float = Field(0.05)
    lookback: int = Field(50)

class AppConfig(BaseModel):
    risk: RiskConfig = RiskConfig()
    model: ModelConfig = ModelConfig()
