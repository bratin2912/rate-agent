
interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({
  message = "Loading...",
}: LoadingSpinnerProps) {
  return (
    <div className="processing-message">
      <div className="spinner" />
      <span>{message}</span>
    </div>
  );
}
