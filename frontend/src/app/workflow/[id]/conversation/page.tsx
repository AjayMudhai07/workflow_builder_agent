"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2, Send, Wifi, WifiOff, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { submitAnswer, getWorkflowStatus } from "@/lib/api/client";
import { useWorkflowWebSocket } from "@/hooks/useWorkflowWebSocket";
import type { QuestionResponse } from "@/lib/api/types";

interface Message {
  role: "assistant" | "user";
  content: string;
  timestamp: Date;
}

export default function ConversationPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [customAnswer, setCustomAnswer] = useState<string>("");
  const [questionNumber, setQuestionNumber] = useState<number>(0);
  const [totalQuestions, setTotalQuestions] = useState<number>(10);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAIThinking, setIsAIThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string>("planning");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [copiedCurrent, setCopiedCurrent] = useState(false);

  // WebSocket connection (TEMPORARILY DISABLED - uncomment when backend is ready)
  const isConnected = false;
  const connectionError = null;

  /*
  const { isConnected, connectionError } = useWorkflowWebSocket({
    workflowId,
    onConnected: () => {
      console.log("WebSocket connected");
    },
    onPhaseChange: (phase) => {
      console.log("Phase changed to:", phase);
      setCurrentPhase(phase);

      // Navigate to plan review if business logic plan is ready
      if (phase === "plan_review") {
        router.push(`/workflow/${workflowId}/plan`);
      }
    },
    onPlannerResponse: (response, responseType) => {
      console.log("Planner response received:", responseType);

      // Stop AI thinking indicator
      setIsAIThinking(false);

      // Add AI's response to messages
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response,
          timestamp: new Date(),
        },
      ]);

      // Update current question
      if (responseType !== "business_logic_plan") {
        setCurrentQuestion(response);
      }

      // Navigate to plan if we got a business logic plan
      if (responseType === "business_logic_plan") {
        setTimeout(() => {
          router.push(`/workflow/${workflowId}/plan`);
        }, 1000);
      }
    },
    onError: (err) => {
      console.error("WebSocket error:", err);
      setError(err);
      setIsAIThinking(false);
    },
  });
  */

  // Extract options from question text (supports both JSON and legacy A-E format)
  const extractOptions = (questionText: string): string[] => {
    // Try to parse as JSON first
    try {
      // Look for JSON object in the text
      const jsonMatch = questionText.match(/\{[\s\S]*"question_type"[\s\S]*"options"[\s\S]*\}/);
      if (jsonMatch) {
        const questionData = JSON.parse(jsonMatch[0]);
        if (questionData.options && Array.isArray(questionData.options)) {
          return questionData.options;
        }
      }
    } catch (e) {
      // Not JSON or invalid JSON, continue with legacy parsing
      console.log("Not JSON format, using legacy parsing");
    }

    // Legacy format: A-E text format
    const lines = questionText.split("\n");
    const options: string[] = [];
    let inOptionsSection = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Check if we're entering the options section
      if (line.toLowerCase().includes("please select one option")) {
        inOptionsSection = true;
        continue;
      }

      // If we're in the options section, extract the option
      if (inOptionsSection) {
        const match = line.match(/^([A-E])\)\s*(.*)$/i);
        if (match) {
          let optionText = match[2].trim();

          // If the option text is incomplete (e.g., ends with "="),
          // look at the next line(s) to get the full text
          let j = i + 1;
          while (j < lines.length && optionText && !lines[j].trim().match(/^[A-E]\)/i)) {
            const nextLine = lines[j].trim();
            if (nextLine) {
              optionText += " " + nextLine;
            }
            j++;
          }

          options.push(optionText || match[1] + ")"); // Fallback to just the letter if empty
        }
      }
    }

    // Fallback to old logic if no options found
    if (options.length === 0) {
      for (const line of lines) {
        const match = line.trim().match(/^([A-E])\)\s*(.+)$/i);
        if (match) {
          options.push(match[2].trim());
        }
      }
    }

    return options;
  };

  // Copy question with options to clipboard
  const copyToClipboard = async (text: string, index?: number) => {
    try {
      await navigator.clipboard.writeText(text);
      if (index !== undefined) {
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
      } else {
        setCopiedCurrent(true);
        setTimeout(() => setCopiedCurrent(false), 2000);
      }
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  // Format question for display (strips JSON if present, returns readable format)
  const formatQuestionForDisplay = (question: string): string => {
    const parsed = parseQuestion(question);

    if (parsed.options.length === 0) {
      return question;
    }

    let formatted = "";
    if (parsed.context) {
      formatted += parsed.context + "\n\n";
    }
    formatted += parsed.question + "\n\n";

    parsed.options.forEach((opt, idx) => {
      const label = String.fromCharCode(65 + idx); // A, B, C, D, E
      formatted += `${label}) ${opt}\n`;
    });

    return formatted.trim();
  };

  // Format question with options for copying
  const formatQuestionForCopy = (question: string): string => {
    return formatQuestionForDisplay(question);
  };

  // Parse question and options (supports both JSON and legacy formats)
  const parseQuestion = (questionText: string): { question: string; context: string; options: string[]; isJson: boolean } => {
    // Try JSON format first
    try {
      const jsonMatch = questionText.match(/\{[\s\S]*"question_type"[\s\S]*"options"[\s\S]*\}/);
      if (jsonMatch) {
        const questionData = JSON.parse(jsonMatch[0]);
        return {
          question: questionData.question || "",
          context: questionData.context || "",
          options: questionData.options || [],
          isJson: true
        };
      }
    } catch (e) {
      console.log("Failed to parse as JSON:", e);
    }

    // Legacy format
    const options = extractOptions(questionText);
    const question = questionText.split("Please select one option:")[0].trim();

    return {
      question,
      context: "",
      options,
      isJson: false
    };
  };

  const parsedQuestion = parseQuestion(currentQuestion);
  const options = parsedQuestion.options;
  const questionText = parsedQuestion.context
    ? `${parsedQuestion.context}\n\n${parsedQuestion.question}`
    : parsedQuestion.question;

  // Load workflow and initial question
  useEffect(() => {
    const loadWorkflow = async () => {
      try {
        setIsLoading(true);

        // Fetch workflow status to get the current question from Planner Agent
        const workflowStatus = await getWorkflowStatus(workflowId);

        // Get the current question from the Planner Agent
        const initialQuestion = workflowStatus.current_question || "Loading question...";

        console.log("=== RAW QUESTION FROM BACKEND ===");
        console.log(initialQuestion);
        console.log("=================================");

        setCurrentQuestion(initialQuestion);

        // Don't add the initial question to messages - it will be shown in the "Current Question" card
        // Messages will only contain the conversation history (user answers and past questions)
        setMessages([]);

        setQuestionNumber(workflowStatus.planner_questions_asked || 0);
      } catch (err: any) {
        console.error("Error loading workflow:", err);
        setError("Failed to load workflow. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    loadWorkflow();
  }, [workflowId]);

  // Handle answer submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    let answer = selectedOption;

    // If "Other" is selected or custom answer provided, use custom answer
    if (selectedOption === "Other (please specify)" || customAnswer.trim()) {
      answer = customAnswer.trim() || selectedOption;
    }

    if (!answer) {
      setError("Please select an option or provide an answer");
      return;
    }

    try {
      // First, add the CURRENT question to history (before it becomes the "previous" question)
      const formattedCurrentQuestion = formatQuestionForDisplay(currentQuestion);

      // Add both the question and the user's answer to messages
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: formattedCurrentQuestion,
          timestamp: new Date(),
        },
        {
          role: "user",
          content: answer,
          timestamp: new Date(),
        },
      ]);

      // Clear the form
      setSelectedOption("");
      setCustomAnswer("");
      setQuestionNumber((prev) => prev + 1);

      // Show "Thinking" indicator immediately (button will be disabled)
      setIsSubmitting(true);
      setIsAIThinking(true);

      // Submit answer to backend (WebSocket will handle the response)
      const response: QuestionResponse = await submitAnswer(
        workflowId,
        answer,
        questionNumber + 1
      );

      // If WebSocket is not connected, handle response directly
      if (!isConnected) {
        setIsAIThinking(false);

        // Check if we got a business logic plan
        if (response.response_type === "business_logic_plan") {
          router.push(`/workflow/${workflowId}/plan`);
          return;
        }

        // Update to the new current question (shown in the Current Question card)
        console.log("Setting new current question:", response.response);
        setCurrentQuestion(response.response);
      }

      // Scroll to bottom
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      }, 100);
    } catch (err: any) {
      console.error("Error submitting answer:", err);
      setError(err.message || "Failed to submit answer. Please try again.");
      setIsAIThinking(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/dashboard")}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
            </div>
            <div className="text-sm text-muted-foreground">
              Step 2 of 5 • Question {questionNumber + 1} of ~{totalQuestions}
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Phase Indicator */}
        <div className="mb-8">
          <PhaseIndicator currentPhase="conversation" />
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              Planning Conversation
            </h1>
            <p className="text-lg text-muted-foreground">
              Help us understand your requirements by answering a few questions
            </p>
          </div>

          {/* WebSocket Connection Error */}
          {connectionError && !isConnected && (
            <Alert variant="destructive">
              <AlertDescription>
                Real-time connection lost: {connectionError}. You can still submit answers, but won't see live updates.
              </AlertDescription>
            </Alert>
          )}

          {/* Chat Conversation */}
          <Card>
            <CardContent className="py-6">
              <div className="space-y-6">
                {/* Conversation History */}
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {message.role === "assistant" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm text-gray-700" style={{ backgroundColor: '#E5E5EA' }}>
                        I
                      </div>
                    )}
                    <div className={`max-w-[75%] space-y-1 ${message.role === "user" ? "items-end" : "items-start"}`}>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-muted-foreground">
                          {message.role === "assistant" ? "IRA" : "You"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                        {message.role === "assistant" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(formatQuestionForCopy(message.content), index)}
                            className="h-5 w-5 p-0"
                          >
                            {copiedIndex === index ? (
                              <Check className="w-3 h-3 text-green-500" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </Button>
                        )}
                      </div>
                      <div
                        className={`text-sm whitespace-pre-wrap leading-relaxed px-4 py-3 rounded-2xl font-semibold ${
                          message.role === "assistant"
                            ? "text-gray-900 dark:text-gray-100 rounded-tl-sm"
                            : "text-white rounded-tr-sm"
                        }`}
                        style={message.role === "assistant" ? { backgroundColor: '#E5E5EA' } : { backgroundColor: '#007AFF' }}
                      >
                        {message.content}
                      </div>
                    </div>
                    {message.role === "user" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm text-white" style={{ backgroundColor: '#007AFF' }}>
                        Y
                      </div>
                    )}
                  </div>
                ))}

                {/* AI Thinking Indicator */}
                {isAIThinking && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm text-gray-700" style={{ backgroundColor: '#E5E5EA' }}>
                      I
                    </div>
                    <div className="max-w-[75%] space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-muted-foreground">IRA</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date().toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="px-4 py-3 rounded-2xl rounded-tl-sm" style={{ backgroundColor: '#E5E5EA' }}>
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-gray-600 dark:text-gray-400" />
                          <span className="text-sm text-gray-900 dark:text-gray-100">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Current Question - only show when NOT loading and NOT thinking */}
                {!isLoading && !isAIThinking && currentQuestion && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm text-gray-700" style={{ backgroundColor: '#E5E5EA' }}>
                      I
                    </div>
                    <div className="flex-1 max-w-[90%] space-y-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-muted-foreground">IRA</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date().toLocaleTimeString()}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(formatQuestionForCopy(currentQuestion))}
                          className="h-5 w-5 p-0"
                        >
                          {copiedCurrent ? (
                            <Check className="w-3 h-3 text-green-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </Button>
                      </div>
                      <div className="text-gray-900 dark:text-gray-100 text-sm whitespace-pre-wrap leading-relaxed font-semibold px-4 py-3 rounded-2xl rounded-tl-sm" style={{ backgroundColor: '#E5E5EA' }}>
                        {questionText}
                      </div>

                      {/* Answer Form */}
                      <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Multiple Choice Options */}
                        {options.length > 0 && (
                          <RadioGroup
                            value={selectedOption}
                            onValueChange={setSelectedOption}
                          >
                            <div className="space-y-2">
                              {options.map((option, index) => {
                                const optionLabel = String.fromCharCode(65 + index); // A, B, C, D, E
                                return (
                                  <div
                                    key={index}
                                    className="flex items-start space-x-2 p-3 rounded-lg border hover:bg-muted/30 transition-colors"
                                  >
                                    <RadioGroupItem
                                      value={option}
                                      id={`option-${index}`}
                                      className="mt-0.5"
                                    />
                                    <Label
                                      htmlFor={`option-${index}`}
                                      className="flex-1 font-normal select-text text-sm"
                                    >
                                      <span className="font-semibold">{optionLabel})</span>{" "}
                                      {option || "(No text provided)"}
                                    </Label>
                                  </div>
                                );
                              })}
                            </div>
                          </RadioGroup>
                        )}

                        {/* Custom Answer (if "Other" selected or no options) */}
                        {(selectedOption.includes("Other") || options.length === 0) && (
                          <div className="space-y-2">
                            <Label htmlFor="custom-answer" className="text-sm">
                              {selectedOption.includes("Other")
                                ? "Please specify:"
                                : "Your answer:"}
                            </Label>
                            <Textarea
                              id="custom-answer"
                              placeholder="Type your answer here..."
                              value={customAnswer}
                              onChange={(e) => setCustomAnswer(e.target.value)}
                              rows={3}
                              className="resize-none text-sm"
                            />
                          </div>
                        )}

                        {/* Error Alert */}
                        {error && (
                          <Alert variant="destructive">
                            <AlertDescription className="text-sm">{error}</AlertDescription>
                          </Alert>
                        )}

                        {/* Submit Button - hidden when AI is thinking */}
                        {!isAIThinking && (
                          <Button
                            type="submit"
                            disabled={
                              isSubmitting ||
                              (!selectedOption && !customAnswer.trim())
                            }
                            className="w-full"
                          >
                            Submit Answer
                            <ArrowRight className="w-4 h-4 ml-2" />
                          </Button>
                        )}
                      </form>
                    </div>
                  </div>
                )}

                {/* Loading State */}
                {isLoading && (
                  <div className="flex flex-col items-center gap-4 py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Loading question...</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card className="bg-muted/50 border-dashed">
            <CardContent className="pt-6">
              <div className="space-y-2 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">Tips:</p>
                <ul className="space-y-1 list-disc list-inside">
                  <li>Answer questions based on your business requirements</li>
                  <li>Select "Other" if you need to provide a custom answer</li>
                  <li>The AI will ask 5-8 questions to fully understand your needs</li>
                  <li>After all questions, you'll review the generated plan</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
