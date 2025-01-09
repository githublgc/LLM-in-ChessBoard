from openai import OpenAI

# 初始化 OpenAI 客户端
client = OpenAI(api_key="your key", base_url="https://api.deepseek.com")

class LLMInterface:
    def __init__(self, model_name: str = "deepseek-chat"):
        self.model_name = model_name
    
    def get_advice(self, prompt: str) -> str:
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert in Gomoku strategy analysis. Summarize the winning strategies based on the provided game data."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()

def read_txt_file(file_path: str) -> str:
    """
    读取 TXT 文件并返回其内容作为字符串。
    """
    with open(file_path, mode='r', encoding='utf-8') as file:
        content = file.read()
    return content

def main():
    # 文件路径
    file_path = "reflexion.txt"
    
    # 读取 TXT 文件内容
    txt_content = read_txt_file(file_path)
    
    # 初始化 LLM 接口
    llm_interface = LLMInterface()
    
    # 生成提示词
    prompt = f"Here is the summary of past Gomoku game strategies:\n{txt_content}\n\nPlease analyze and summarize the winning strategies."
    
    # 调用 API 获取建议
    advice = llm_interface.get_advice(prompt)
    
    # 输出结果
    print("Winning Strategies Summary:\n")
    print(advice)

if __name__ == "__main__":
    main()