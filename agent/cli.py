import sys
from agent.pipeline import run_multi_agent_pipeline
from agent.llm import call_llm_chat

def print_banner():
    print("=" * 60)
    print("   FINANCIAL RESEARCH AGENT - INTERACTIVE CLI")
    print("=" * 60)

def main():
    print_banner()
    ticker = input("\nEnter a stock ticker to research (e.g. AAPL): ").strip().upper()
    if not ticker:
        print("Invalid ticker. Exiting.")
        sys.exit(1)
        
    print(f"\n[!] Initializing Multi-Agent Pipeline for {ticker}...")
    
    # 1. Run the pipeline to generate the report and state
    state = run_multi_agent_pipeline(ticker, interactive_feedback=True)
    
    if not state.final_report:
        print("\n[!] Failed to generate the investment brief. Exiting.")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("   REPORT GENERATED SUCCESSFULLY")
    print("=" * 60)
    print("\nYou can now ask follow-up questions about this company or the report.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    # 2. Build the initial system context for the chat
    system_content = (
        f"You are a helpful Financial Research Assistant answering questions about {ticker}. "
        "Use the following finalized investment brief and raw data context to answer user questions.\n\n"
        f"--- FINAL REPORT ---\n{state.final_report}\n\n"
        f"--- RAW DATA GLIMPSE ---\nStock Metrics: {state.raw_data.get('stock_data', {})}\n"
        f"News Headlines: {state.raw_data.get('news_data', [])}\n"
    )
    
    state.chat_history.append({"role": "system", "content": system_content})
    
    # 3. Enter the Interactive Chat Loop
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("\nEnding session. Goodbye!")
                break
            
            if not user_input:
                continue
                
            # Append user question
            state.chat_history.append({"role": "user", "content": user_input})
            
            # Send the entire history to the LLM
            print("Agent: Thinking...")
            answer = call_llm_chat(state.chat_history)
            
            # Print and append the assistant's answer
            print(f"Agent: {answer}\n")
            state.chat_history.append({"role": "assistant", "content": answer})
            
        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[!] Error during chat: {e}\n")

if __name__ == "__main__":
    main()

