// Claude 3.5 Sonnet was used to help write this code.
import { useState, useEffect, useRef } from "react";

interface SolverProps {
  // The URL of the solver websocket
  url: string;

  // Runs when the websocket is connected
  onConnect?: () => void;

  // Runs when the websocket is disconnected
  onDisconnect?: () => void;

  // Runs when an error occurs
  onError?: (event: Event) => void;

  // Runs when a proof step is received
  onProofStep?: (proof: string) => void;
}

/**
 * Connects to the solver websocket and returns the proof steps and final proof
 * @param url - The URL of the solver websocket
 * @param onConnect - Runs when the websocket is connected
 * @param onDisconnect - Runs when the websocket is disconnected
 * @param onError - Runs when an error occurs
 * @param onProofStep - Runs when a proof step is received
 * @returns The proof steps, final proof, connection state, and start function
 */
export default function useSolver({
  url,
  onConnect,
  onDisconnect,
  onError,
  onProofStep,
}: SolverProps) {
  const [proofSteps, setProofSteps] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [finalProof, setFinalProof] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const start = (initialCode: String) => {
    // Clean up existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Reset states
    setProofSteps([]);
    setFinalProof(null);
    setIsConnected(false);
    setGenerating(false);

    // Create WebSocket connection
    const ws = new WebSocket(url);
    wsRef.current = ws;

    console.log("Attempting to connect to solver websocket");

    ws.onopen = () => {
      setIsConnected(true);
      setGenerating(true);
      console.log("Connected to solver websocket");
      onConnect?.();

      ws.send(initialCode.toString()); // SENDING USERS THEOREM TO BACKEND
    };

    ws.onmessage = (event) => {
      const proof = event.data;

      // Add new proof variation to the list
      setProofSteps((prev) => [...prev, proof]);

      // Check if this is the final correct proof
      if (proof.includes("PROOF_COMPLETE")) {
        setFinalProof(proof);
        setGenerating(false);
        ws.close();
      }

      onProofStep?.(proof);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setGenerating(false);
      console.log("Disconnected from solver websocket");
      onDisconnect?.();
    };

    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      setGenerating(false);
      onError?.(event);
    };
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    proofSteps,
    isConnected,
    finalProof,
    generating,
    start,
    currentStep: proofSteps.length,
  };
}
