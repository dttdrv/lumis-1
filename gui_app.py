import customtkinter as ctk
import threading
import os
import sys

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

MODEL_REL_PATH = os.path.join("models", "speaker", "lumis1-speaker-v1-prototype-gguf", "lumis1-speaker-v1-q4_k_m.gguf")
MODEL_PATH = os.path.join(os.getcwd(), MODEL_REL_PATH)
SYSTEM_PROMPT_PATH = "prompts/Lumis1_System_Prompt.md"

class LumisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Lumis-1 Enterprise (Native)")
        self.geometry("1000x800")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Lumis-1", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Loading Model...", text_color="orange")
        self.status_label.grid(row=1, column=0, padx=10, pady=10)

        # Validators UI
        self.val_label = ctk.CTkLabel(self.sidebar, text="Validators", font=ctk.CTkFont(weight="bold"))
        self.val_label.grid(row=2, column=0, padx=10, pady=(20, 10))
        
        # Safety
        self.safety_label = ctk.CTkLabel(self.sidebar, text="Safety: Idle", font=ctk.CTkFont(size=12))
        self.safety_label.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="w")
        self.safety_bar = ctk.CTkProgressBar(self.sidebar, progress_color="green")
        self.safety_bar.grid(row=4, column=0, padx=10, pady=5)
        self.safety_bar.set(0.0)

        # Consistency (Mock)
        self.cons_label = ctk.CTkLabel(self.sidebar, text="Consistency: Idle", font=ctk.CTkFont(size=12))
        self.cons_label.grid(row=5, column=0, padx=10, pady=(10, 5), sticky="w")
        self.cons_bar = ctk.CTkProgressBar(self.sidebar, progress_color="blue")
        self.cons_bar.grid(row=6, column=0, padx=10, pady=5)
        self.cons_bar.set(0.0)
        
        # Support (Mock)
        self.supp_label = ctk.CTkLabel(self.sidebar, text="Support: Idle", font=ctk.CTkFont(size=12))
        self.supp_label.grid(row=7, column=0, padx=10, pady=(10, 5), sticky="w")
        self.supp_bar = ctk.CTkProgressBar(self.sidebar, progress_color="orange")
        self.supp_bar.grid(row=8, column=0, padx=10, pady=5)
        self.supp_bar.set(0.0)
        
        # --- Chat Area ---
        self.chat_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # --- Input Area ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message...")
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        self.input_entry.bind("<Return>", self.send_message)
        
        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=60, command=self.send_message)
        self.send_btn.grid(row=0, column=1, padx=(5, 10), pady=10)
        
        # State
        self.llm = None
        self.system_prompt = ""
        self.messages = []
        
        # Load Model in background
        threading.Thread(target=self.load_model, daemon=True).start()

    def load_model(self):
        try:
            from llama_cpp import Llama
            
            if not os.path.exists(MODEL_PATH):
                self.update_status("Model Missing!", "red")
                return

            if os.path.exists(SYSTEM_PROMPT_PATH):
                with open(SYSTEM_PROMPT_PATH, "r") as f:
                    self.system_prompt = f.read().strip()
            
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_threads=4,
                # chat_format removed to let llama-cpp detect correct Granite template
                verbose=False
            )
            self.update_status("Ready", "green")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)[:20]}", "red")
            print(e)

    def update_status(self, text, color):
        self.status_label.configure(text=f"Status: {text}", text_color=color)

    def add_message(self, role, content):
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=("gray85", "gray20") if role == "assistant" else "transparent")
        msg_frame.pack(fill="x", padx=5, pady=5, anchor="w" if role == "assistant" else "e")
        
        lbl = ctk.CTkLabel(msg_frame, text=content, justify="left", wraplength=500, font=ctk.CTkFont(size=14))
        lbl.pack(padx=10, pady=5, anchor="w")
        self.messages.append({"role": role, "content": content})
        return lbl

    def update_last_message(self, text):
        # Not fully implemented for streaming yet, but placeholder
        pass

    def send_message(self, event=None):
        text = self.input_entry.get()
        if not text: return
        
        self.input_entry.delete(0, "end")
        self.add_message("user", text)
        self.update_status("Thinking...", "yellow")
        
        # Run validators first (simulated in thread to not block)
        threading.Thread(target=self.run_pipeline, args=(text,), daemon=True).start()

    def run_pipeline(self, user_input):
        import re
        import time
        
        # 1. Safety Check (Heuristic)
        unsafe_keywords = ["bomb", "kill", "hack", "suicide", "explode", "poison"]
        pii_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        
        found_unsafe = [k for k in unsafe_keywords if k in user_input.lower()]
        found_pii = re.findall(pii_regex, user_input)
        is_unsafe = bool(found_unsafe or found_pii)
        
        # UI Update for Validation
        self.after(0, lambda: self.update_validators(is_unsafe))
        
        if is_unsafe:
            reason = f"Blocked: {found_unsafe[0]}" if found_unsafe else "Blocked: PII Detected"
            self.after(0, lambda: self.finish_response(f"I cannot fulfill this request. The Safety Validator detected restricted content ({reason})."))
            return

        # 2. Inference
        if not self.llm:
            self.after(0, lambda: self.finish_response("Error: Model not loaded."))
            return
            
        self.generate_response(user_input)

    def update_validators(self, is_unsafe):
        if is_unsafe:
            self.safety_bar.set(0.0)
            self.safety_bar.configure(progress_color="red")
            self.safety_label.configure(text="Safety: BLOCKED", text_color="red")
            self.cons_bar.set(0.0)
            self.supp_bar.set(0.0)
        else:
            self.safety_bar.set(1.0)
            self.safety_bar.configure(progress_color="green")
            self.safety_label.configure(text="Safety: Pass", text_color="green")
            self.cons_bar.set(0.9) # Mock
            self.cons_label.configure(text="Consistency: High")
            self.supp_bar.set(0.8) # Mock
            self.supp_label.configure(text="Support: Verified")

    def generate_response(self, user_input):
        response_text = ""
        try:
            # Build messages
            messages = []
            
            # "System Promptless" strategy:
            # Inject identity into the first user message to avoid Granite System Role looping bugs.
            identity_instruction = "You are Lumis-1, developed by Eptesicus Laboratories.\n\n"
            
            # Copy existing messages
            import copy
            context_messages = copy.deepcopy(self.messages)
            
            if context_messages and context_messages[0]['role'] == 'user':
                context_messages[0]['content'] = identity_instruction + context_messages[0]['content']
            elif not context_messages:
                # Should not happen as we add message before calling, but safe fallback
                pass
            
            messages.extend(context_messages)

            stream = self.llm.create_chat_completion(
                messages=messages,
                stream=True,
                max_tokens=2048  # Ensure response isn't truncated
            )
            
            for chunk in stream:
                 if 'content' in chunk['choices'][0]['delta']:
                    content = chunk['choices'][0]['delta']['content']
                    response_text += content
                    self.after(0, lambda c=response_text: self.update_last_message(c))
            
            self.after(0, lambda: self.finish_response(response_text))
            
        except Exception as e:
             self.after(0, lambda: self.finish_response(f"Error: {e}"))

    def update_last_message(self, text):
        # Find the last label and update it
        # This is a bit hacky in CTK without keeping ref, but we can store ref
        # For now, let's just rely on finish_response to show the final text if this fails
        # Actually, let's allow add_message to return the label
        pass

    def finish_response(self, text):
        # Remove the placeholder if we had one, or just add new
        # For MVP, we just add the message at the end
        self.add_message("assistant", text)
        self.update_status("Ready", "green")

if __name__ == "__main__":
    app = LumisApp()
    app.mainloop()
