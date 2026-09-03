from typing import List, Dict, Any
from pydantic import BaseModel
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger

class WeatherRisk(BaseModel):
    risk_type: str
    severity: int  # 0 to 100
    description: str
    recommended_actions: List[str]

class WeatherRiskAssessor:
    """Assesses generic weather risks based on forecasts."""
    
    def assess_risks(self, forecast: List[Dict[str, Any]]) -> List[WeatherRisk]:
        """Assess various weather risks for a given forecast period."""
        risks = []
        
        if not forecast:
            return risks

        # Check for Heat Stress, Cold/Frost, Waterlogging, Wind over the forecast
        max_temp = max([day.get("temperature", 0) for day in forecast])
        min_temp = min([day.get("temperature", 100) for day in forecast])
        max_rain = max([day.get("rainfall", 0) for day in forecast])
        max_wind = max([day.get("wind_speed", 0) for day in forecast])
        
        # Drought risk: no rain for 7+ days + high temp
        rain_days = sum([1 for day in forecast if day.get("rainfall", 0) > 0])
        avg_temp = sum([day.get("temperature", 0) for day in forecast]) / len(forecast)

        if max_temp > 40:
            risks.append(WeatherRisk(
                risk_type="Heat Stress",
                severity=min(100, int((max_temp - 40) * 10 + 50)),
                description=f"High temperatures up to {max_temp}°C expected.",
                recommended_actions=["Increase irrigation frequency", "Provide shade if possible"]
            ))

        if min_temp < 5:
            risks.append(WeatherRisk(
                risk_type="Cold/Frost",
                severity=min(100, int((5 - min_temp) * 10 + 50)),
                description=f"Low temperatures down to {min_temp}°C expected, risking frost.",
                recommended_actions=["Apply light irrigation in the evening", "Use frost covers"]
            ))

        if max_rain > 50:
            risks.append(WeatherRisk(
                risk_type="Waterlogging",
                severity=min(100, int((max_rain - 50) + 50)),
                description=f"Heavy rainfall of {max_rain}mm expected.",
                recommended_actions=["Ensure proper field drainage", "Delay fertilizer application"]
            ))

        if len(forecast) >= 7 and rain_days == 0 and avg_temp > 30:
            risks.append(WeatherRisk(
                risk_type="Drought",
                severity=80,
                description="Extended dry period with high temperatures.",
                recommended_actions=["Implement water conservation measures", "Use mulching to retain soil moisture"]
            ))

        if max_wind > 40:
            risks.append(WeatherRisk(
                risk_type="Strong Wind",
                severity=min(100, int((max_wind - 40) * 1.5 + 50)),
                description=f"Strong winds up to {max_wind} km/h expected.",
                recommended_actions=["Provide mechanical support to tall crops", "Delay pesticide spraying"]
            ))

        # High humidity disease risk
        consecutive_humid_days = 0
        for day in forecast:
            if day.get("humidity", 0) > 85:
                consecutive_humid_days += 1
                if consecutive_humid_days >= 3:
                    risks.append(WeatherRisk(
                        risk_type="High Humidity Disease",
                        severity=75,
                        description="Prolonged high humidity conditions favorable for fungal diseases.",
                        recommended_actions=["Monitor for fungal infections", "Apply preventive fungicides if necessary"]
                    ))
                    break
            else:
                consecutive_humid_days = 0

        # Hailstorm risk (simplified mock based on generic 'weather_code')
        for day in forecast:
            if day.get("weather_code") in [96, 99]: # Example codes for hail
                risks.append(WeatherRisk(
                    risk_type="Hailstorm",
                    severity=90,
                    description="Hailstorm expected.",
                    recommended_actions=["Use anti-hail nets if available"]
                ))
                break

        return risks

    def aggregate_risk_score(self, risks: List[WeatherRisk]) -> int:
        """Aggregate multiple risks into a single score 0-100."""
        if not risks:
            return 0
        return min(100, max([risk.severity for risk in risks]))

    def get_risk_color(self, score: int) -> str:
        """Map risk score to a color code."""
        if score < 30:
            return "GREEN"
        elif score < 60:
            return "YELLOW"
        elif score < 80:
            return "ORANGE"
        else:
            return "RED"
