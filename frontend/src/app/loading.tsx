export default function Loading() {
 return (
 <div className="p-6 max-w-5xl mx-auto animate-pulse" aria-label="Loading...">
 {/* Page title skeleton */}
 <div className="h-7 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700/60 rounded-xl w-48 mb-2" />
 <div className="h-4 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700/60 rounded-lg w-72 mb-8" />

 {/* Stats row */}
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
 {[...Array(4)].map((_, i) => (
 <div key={i} className="h-28 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700/60 rounded-2xl" />
 ))}
 </div>

 {/* Content cards */}
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
 {[...Array(6)].map((_, i) => (
 <div key={i} className="h-36 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700/60 rounded-2xl" />
 ))}
 </div>
 </div>
 );
}
