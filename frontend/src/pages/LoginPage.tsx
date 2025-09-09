type LoginPageProps = {
  onSubmit: () => void;
};

export default function LoginPage({ onSubmit }: LoginPageProps) {
  return (
    <div className="max-w-sm space-y-3">
      <input className="w-full border rounded px-3 py-2" placeholder="Email" />
      <input className="w-full border rounded px-3 py-2" type="password" placeholder="Password" />
      <button className="rounded bg-blue-600 px-4 py-2 text-white" onClick={onSubmit}>
        Sign in
      </button>
    </div>
  );
}
