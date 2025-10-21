"use client";

import React, { useState, useEffect, useRef } from "react";
import { Bot, User, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";

export interface ConversationMessage {
  role: "ai" | "user";
  content: string;
  options?: string[];
  timestamp: Date;
}

interface ConversationViewProps {
  messages: ConversationMessage[];
  currentQuestion?: string;
  currentOptions?: string[];
  questionNumber?: number;
  totalQuestions?: number;
  isLoading?: boolean;
  onSubmitAnswer: (answer: string, additionalNotes?: string) => void;
  className?: string;
}

export function ConversationView({
  messages,
  currentQuestion,
  currentOptions = [],
  questionNumber = 1,
  totalQuestions = 8,
  isLoading = false,
  onSubmitAnswer,
  className,
}: ConversationViewProps) {
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [additionalNotes, setAdditionalNotes] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to latest message
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentQuestion]);

  const handleSubmit = () => {
    if (!selectedOption) return;

    onSubmitAnswer(selectedOption, additionalNotes);
    setSelectedOption("");
    setAdditionalNotes("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    // Handle keyboard shortcuts: 1-5 for options A-E
    if (e.key >= "1" && e.key <= "5") {
      const index = parseInt(e.key) - 1;
      if (currentOptions[index]) {
        setSelectedOption(currentOptions[index]);
      }
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)} onKeyDown={handleKeyPress}>
      {/* Progress Header */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b">
        <h2 className="text-lg font-semibold">Interactive Conversation</h2>
        <div className="text-sm text-muted-foreground">
          Question {questionNumber} of ~{totalQuestions}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {/* Previous Messages */}
        {messages.map((message, index) => (
          <div
            key={index}
            className={cn(
              "flex gap-3",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {message.role === "ai" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary" />
              </div>
            )}

            <Card
              className={cn(
                "max-w-[80%] p-4",
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              {message.options && message.options.length > 0 && (
                <div className="mt-3 space-y-1 text-xs opacity-70">
                  {message.options.map((opt, i) => (
                    <div key={i}>Selected: {opt}</div>
                  ))}
                </div>
              )}
            </Card>

            {message.role === "user" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <User className="w-5 h-5 text-primary-foreground" />
              </div>
            )}
          </div>
        ))}

        {/* Current AI Question */}
        {currentQuestion && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary" />
            </div>

            <Card className="flex-1 p-4 bg-muted border-2 border-primary/20">
              <p className="text-sm whitespace-pre-wrap mb-4">{currentQuestion}</p>

              {/* Options */}
              {currentOptions.length > 0 && (
                <RadioGroup value={selectedOption} onValueChange={setSelectedOption}>
                  <div className="space-y-2">
                    {currentOptions.map((option, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <RadioGroupItem
                          value={option}
                          id={`option-${index}`}
                          className="mt-0.5"
                        />
                        <Label
                          htmlFor={`option-${index}`}
                          className="text-sm cursor-pointer flex-1 leading-relaxed"
                        >
                          {option}
                        </Label>
                      </div>
                    ))}
                  </div>
                </RadioGroup>
              )}
            </Card>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary" />
            </div>

            <Card className="p-4 bg-muted">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>AI is thinking...</span>
              </div>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Response Form */}
      {currentQuestion && !isLoading && (
        <Card className="p-4 border-2">
          <div className="space-y-4">
            <div>
              <Label htmlFor="additional-notes" className="text-sm font-medium">
                Additional notes (optional)
              </Label>
              <Textarea
                id="additional-notes"
                placeholder="Add any clarifications or details..."
                value={additionalNotes}
                onChange={(e) => setAdditionalNotes(e.target.value)}
                className="mt-2 min-h-[80px]"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="text-xs text-muted-foreground">
                Tip: Use keys 1-5 for quick selection
              </div>
              <Button
                onClick={handleSubmit}
                disabled={!selectedOption}
                size="lg"
              >
                Submit Answer →
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Conversation History Toggle */}
      {messages.length > 0 && (
        <Accordion type="single" collapsible className="mt-4">
          <AccordionItem value="history" className="border-0">
            <AccordionTrigger className="text-sm hover:no-underline">
              View Conversation History ({messages.length} messages)
            </AccordionTrigger>
            <AccordionContent>
              <div className="text-xs text-muted-foreground space-y-2 max-h-[200px] overflow-y-auto">
                {messages.map((msg, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="font-semibold">
                      {msg.role === "ai" ? "Q:" : "A:"}
                    </span>
                    <span className="flex-1">
                      {msg.content.substring(0, 100)}
                      {msg.content.length > 100 ? "..." : ""}
                    </span>
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}
    </div>
  );
}
