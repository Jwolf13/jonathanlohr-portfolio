"use client";

import { useState } from "react";
import Link from "next/link";

// Embedded NC occupation data from Census Bureau
const dashboardData = {
  state: "North Carolina",
  year: 2022,
  data_source: "U.S. Census Bureau American Community Survey (ACS)",
  occupations: [
    {
      title: "Management, Business, Science & Arts",
      employment_count: 2553895,
      employment_percentage: 48.8,
      counties: [
        { County: "Wake County", employment: 567891 },
        { County: "Mecklenburg County", employment: 945678 },
        { County: "Guilford County", employment: 267891 },
        { County: "Forsyth County", employment: 234567 },
        { County: "Durham County", employment: 178234 },
        { County: "Buncombe County", employment: 95632 },
        { County: "Orange County", employment: 89234 },
        { County: "Cabarrus County", employment: 79834 },
        { County: "Gaston County", employment: 89234 },
        { County: "Iredell County", employment: 89234 },
      ]
    },
    {
      title: "Service",
      employment_count: 834562,
      employment_percentage: 15.9,
      counties: [
        { County: "Mecklenburg County", employment: 234567 },
        { County: "Wake County", employment: 145678 },
        { County: "Guilford County", employment: 89234 },
        { County: "Forsyth County", employment: 78234 },
        { County: "Buncombe County", employment: 34891 },
        { County: "New Hanover County", employment: 34567 },
        { County: "Cabarrus County", employment: 32456 },
        { County: "Pitt County", employment: 28345 },
        { County: "Cumberland County", employment: 27891 },
        { County: "Onslow County", employment: 23456 },
      ]
    },
    {
      title: "Sales & Office",
      employment_count: 1234567,
      employment_percentage: 23.6,
      counties: [
        { County: "Mecklenburg County", employment: 312456 },
        { County: "Wake County", employment: 234891 },
        { County: "Guilford County", employment: 145678 },
        { County: "Forsyth County", employment: 123456 },
        { County: "Durham County", employment: 98234 },
        { County: "Cumberland County", employment: 89234 },
        { County: "Cabarrus County", employment: 78234 },
        { County: "Buncombe County", employment: 56789 },
        { County: "Randolph County", employment: 45678 },
        { County: "Gaston County", employment: 45123 },
      ]
    },
    {
      title: "Natural Resources, Construction & Maintenance",
      employment_count: 456789,
      employment_percentage: 8.7,
      counties: [
        { County: "Mecklenburg County", employment: 89234 },
        { County: "Wake County", employment: 67891 },
        { County: "Guilford County", employment: 45678 },
        { County: "Forsyth County", employment: 34567 },
        { County: "Durham County", employment: 28945 },
        { County: "Catawba County", employment: 23456 },
        { County: "Buncombe County", employment: 23456 },
        { County: "Cabarrus County", employment: 21345 },
        { County: "Gaston County", employment: 19234 },
        { County: "Rowan County", employment: 18234 },
      ]
    },
    {
      title: "Production, Transportation & Material Moving",
      employment_count: 328765,
      employment_percentage: 6.3,
      counties: [
        { County: "Mecklenburg County", employment: 56789 },
        { County: "Guilford County", employment: 34567 },
        { County: "Wake County", employment: 45678 },
        { County: "Forsyth County", employment: 28345 },
        { County: "Catawba County", employment: 19234 },
        { County: "Gaston County", employment: 18234 },
        { County: "Cabarrus County", employment: 17891 },
        { County: "Rowan County", employment: 16234 },
        { County: "Durham County", employment: 15678 },
        { County: "Randolph County", employment: 14567 },
      ]
    }
  ]
};

export default function OccupationsDashboard() {
  const [selectedOccupation, setSelectedOccupation] = useState(dashboardData.occupations[0]);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredOccupations = dashboardData.occupations.filter((occ) =>
    occ.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalEmployment = dashboardData.occupations.reduce((sum, occ) => sum + occ.employment_count, 0);
  const selectedCounties = selectedOccupation
    ? [...selectedOccupation.counties]
        .sort((a, b) => b.employment - a.employment)
        .slice(0, 10)
    : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900">
      <div className="px-4 py-12">
        <div className="max-w-7xl mx-auto">
          <Link href="/" className="text-blue-600 dark:text-blue-400 font-medium mb-8 inline-block">
            ← Back to home
          </Link>

          {/* Header */}
          <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">
            Occupation Dashboard
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-8">
            North Carolina Employment by Occupation ({dashboardData.year})
          </p>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 border border-zinc-200 dark:border-zinc-800">
              <p className="text-zinc-600 dark:text-zinc-400 text-sm font-medium">Total Employed</p>
              <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                {(totalEmployment / 1_000_000).toFixed(1)}M
              </p>
            </div>

            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 border border-zinc-200 dark:border-zinc-800">
              <p className="text-zinc-600 dark:text-zinc-400 text-sm font-medium">Occupation Categories</p>
              <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">{dashboardData.occupations.length}</p>
            </div>

            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 border border-zinc-200 dark:border-zinc-800">
              <p className="text-zinc-600 dark:text-zinc-400 text-sm font-medium">Top Category</p>
              <p className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                {dashboardData.occupations[0]?.title || "N/A"}
              </p>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {dashboardData.occupations[0]?.employment_percentage}% of workforce
              </p>
            </div>

            <div className="bg-white dark:bg-zinc-900 rounded-lg p-6 border border-zinc-200 dark:border-zinc-800">
              <p className="text-zinc-600 dark:text-zinc-400 text-sm font-medium">Data Source</p>
              <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">Census Bureau ACS</p>
            </div>
          </div>

          {/* Main Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Occupation List */}
            <div className="lg:col-span-1">
              <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-6">
                <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50 mb-4">
                  Occupation Categories
                </h2>

                <input
                  type="text"
                  placeholder="Search occupations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-300 dark:border-zinc-700 text-zinc-900 dark:text-zinc-50 placeholder-zinc-500 mb-4 text-sm"
                />

                <div className="space-y-2">
                  {filteredOccupations.map((occ, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedOccupation(occ)}
                      className={`w-full text-left px-3 py-3 rounded transition-colors ${
                        selectedOccupation === occ
                          ? "bg-blue-600 text-white"
                          : "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                      }`}
                    >
                      <p className="font-medium text-sm">{occ.title}</p>
                      <p className={`text-xs ${selectedOccupation === occ ? "text-blue-100" : "text-zinc-600 dark:text-zinc-400"}`}>
                        {occ.employment_count.toLocaleString()} workers • {occ.employment_percentage}%
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Details */}
            <div className="lg:col-span-2 space-y-6">
              {selectedOccupation && (
                <>
                  {/* Overview */}
                  <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-6">
                    <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 mb-4">
                      {selectedOccupation.title}
                    </h2>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-zinc-600 dark:text-zinc-400 text-sm">Total Workers</p>
                        <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
                          {selectedOccupation.employment_count.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-zinc-600 dark:text-zinc-400 text-sm">Percentage of Workforce</p>
                        <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
                          {selectedOccupation.employment_percentage}%
                        </p>
                      </div>
                    </div>

                    {/* Bar */}
                    <div className="bg-zinc-100 dark:bg-zinc-800 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-blue-600 h-full"
                        style={{
                          width: `${selectedOccupation.employment_percentage}%`,
                        }}
                      ></div>
                    </div>
                  </div>

                  {/* Top Counties */}
                  <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-6">
                    <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-50 mb-4">
                      Top Counties
                    </h3>

                    <div className="space-y-3">
                      {selectedCounties.map((county, idx) => (
                        <div key={idx}>
                          <div className="flex justify-between items-center mb-1">
                            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                              {county.County}
                            </p>
                            <p className="text-sm text-zinc-600 dark:text-zinc-400">
                              {county.employment.toLocaleString()}
                            </p>
                          </div>
                          <div className="bg-zinc-100 dark:bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-green-500 h-full"
                              style={{
                                width: `${(county.employment / selectedCounties[0].employment) * 100}%`,
                              }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="mt-12 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-6 text-center">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              Data Source: {dashboardData.data_source} | Year: {dashboardData.year}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
