export default function DashboardLoading() {
  return (
    <div className="p-8">
      <div className="skeleton h-6 w-48 rounded-md" />
      <div className="skeleton mt-3 h-4 w-96 rounded-md" />
      <div className="skeleton mt-6 h-32 w-full rounded-lg" />
      <div className="mt-6 space-y-2">
        <div className="skeleton h-12 w-full rounded-lg" />
        <div className="skeleton h-12 w-full rounded-lg" />
        <div className="skeleton h-12 w-full rounded-lg" />
      </div>
    </div>
  );
}
