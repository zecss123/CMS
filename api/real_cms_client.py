import requests
import json
import pandas as pd
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime, timedelta

class RealCMSAPIClient:
    """真实的CMS API客户端"""
    
    def __init__(self, base_url: str = "http://172.16.253.39", timeout: int = 100):
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "CMS-Client/1.0"
        }
        
    def fetch_vibration_data(self, region: str, station: str, position: str, 
                           point: str, features: str, start_time: str, end_time: str) -> pd.DataFrame:
        """获取振动数据"""
        url = f"{self.base_url}/api/model/services/6853afa7540afad16e5114f8"
        
        payload = {
            "content": {
                "input": {
                    "region_": region,
                    "station_": f"`{station}`",
                    "position": f"`{position}`",
                    "point_": point,
                    "Features": features,
                    "start_time": start_time,
                    "end_time": end_time
                }
            }
        }
        
        try:
            logger.info(f"请求振动数据: {region}-{station}-{position}-{point}")
            response = requests.post(
                url=url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 解析双重转义的output字段
            output_str = result['output']
            decoded_output = json.loads(output_str.encode('utf-8').decode('unicode_escape'))
            
            # 转换为DataFrame
            df = pd.DataFrame.from_dict(decoded_output)
            if not df.empty:
                df['Time'] = pd.to_datetime(df['Time'] + 28800000, unit='ns')
                
                # 简化列名
                column_mapping = {}
                for col in df.columns:
                    if 'Sample_Rate' in col:
                        column_mapping[col] = 'Sample_Rate'
                    elif 'Speed' in col:
                        column_mapping[col] = 'Speed'
                    elif 'Time_Domain_RMS_Value' in col:
                        column_mapping[col] = 'Time_Domain_RMS_Value'
                    elif 'Time_Domain_10_5000Hz_Acceleration_RMS' in col:
                        column_mapping[col] = 'Time_Domain_10_5000Hz_Acceleration_RMS'
                
                df = df.rename(columns=column_mapping)
                
            logger.info(f"成功获取 {len(df)} 条振动数据记录")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return pd.DataFrame()
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"响应解析失败: {e}")
            return pd.DataFrame()
    
    def run_analysis_model(self, model_id: str, wfid: str, run_date: str = "0") -> str:
        """运行分析模型"""
        url = f"{self.base_url}/api/model/services/681c0f2e016a0cd2dd73295f"
        
        payload = {
            "content": {
                "input": {
                    "run_date": run_date,
                    "model_id": model_id,
                    "wfid": wfid
                }
            }
        }
        
        try:
            logger.info(f"运行分析模型: model_id={model_id}, wfid={wfid}")
            response = requests.post(
                url=url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 解析模型输出
            if 'output' in result:
                output_str = result['output']
                try:
                    decoded_output = json.loads(output_str.encode('utf-8').decode('unicode_escape'))
                    model_result = str(decoded_output)
                except:
                    model_result = output_str
            else:
                model_result = "模型分析完成，未返回详细结果"
                
            logger.info("模型分析完成")
            return model_result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"模型API请求失败: {e}")
            return f"模型分析失败: {str(e)}"
        except Exception as e:
            logger.error(f"模型结果解析失败: {e}")
            return f"模型结果解析失败: {str(e)}"
    
    def generate_chart(self, region: str, station: str, position: str, 
                      point: str, features: str, start_time: str, end_time: str, 
                      output_path: Optional[str] = None) -> str:
        """生成图表（基于真实数据）"""
        try:
            # 获取真实数据
            df = self.fetch_vibration_data(region, station, position, point, features, start_time, end_time)
            
            if df.empty:
                logger.warning("无数据可用于生成图表")
                return ""
            
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'CMS振动分析图表 - {region}-{station}-{position}-{point}', fontsize=16)
            
            # 绘制各个指标的时间序列
            if 'Time_Domain_RMS_Value' in df.columns:
                axes[0, 0].plot(df['Time'], df['Time_Domain_RMS_Value'], 'b-', linewidth=2)
                axes[0, 0].set_title('RMS值趋势')
                axes[0, 0].set_ylabel('RMS值')
                axes[0, 0].grid(True, alpha=0.3)
                axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            if 'Speed' in df.columns:
                axes[0, 1].plot(df['Time'], df['Speed'], 'r-', linewidth=2)
                axes[0, 1].set_title('转速趋势')
                axes[0, 1].set_ylabel('转速 (RPM)')
                axes[0, 1].grid(True, alpha=0.3)
                axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            if 'Time_Domain_10_5000Hz_Acceleration_RMS' in df.columns:
                axes[1, 0].plot(df['Time'], df['Time_Domain_10_5000Hz_Acceleration_RMS'], 'g-', linewidth=2)
                axes[1, 0].set_title('加速度RMS趋势')
                axes[1, 0].set_ylabel('加速度RMS')
                axes[1, 0].grid(True, alpha=0.3)
                axes[1, 0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            # 数据分布直方图
            if 'Time_Domain_RMS_Value' in df.columns:
                axes[1, 1].hist(df['Time_Domain_RMS_Value'], bins=20, alpha=0.7, color='blue')
                axes[1, 1].set_title('RMS值分布')
                axes[1, 1].set_xlabel('RMS值')
                axes[1, 1].set_ylabel('频次')
                axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if output_path is None:
                output_path = f"real_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"图表已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"图表生成失败: {e}")
            return ""
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            # 使用一个简单的请求测试连接
            test_data = self.fetch_vibration_data(
                region="A08",
                station="1003", 
                position="8",
                point="AI_CMS024",
                features="Sample_Rate,Speed",
                start_time=(datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            return not test_data.empty
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False